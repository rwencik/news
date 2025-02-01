# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline, set_seed

app = FastAPI()

# Set a seed for reproducibility
set_seed(42)

# Load models with error handling
try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception as e:
    print(f"Error loading summarization model: {e}")
    summarizer = None

try:
    translator = pipeline(
        "translation", 
        model="Helsinki-NLP/opus-mt-en-ROMANCE"  # Fully free, no token required
    )
except Exception as e:
    print(f"Error loading translation model: {e}")
    translator = None

class NewsRequest(BaseModel):
    text: str
    max_summary_length: int = 130
    min_summary_length: int = 40

@app.post("/process-news")
async def process_news(request: NewsRequest):
    try:
        if not summarizer:
            return {"error": "Summarization model is not available"}
        if not translator:
            return {"error": "Translation model is not available"}

        # Summarize with repetition control
        summary = summarizer(
            request.text,
            max_length=request.max_summary_length,
            min_length=request.min_summary_length,
            repetition_penalty=2.5  # Higher penalty for repetition
        )[0]['summary_text']

        # Prepend language token for Portuguese
        text_with_lang_token = f">>pt<< {summary}"

        # Translate summary to Brazilian Portuguese
        translation = translator(
            text_with_lang_token,
            max_length=request.max_summary_length + 20  # Allow slightly longer translations
        )[0]['translation_text']

        return {
            "original_summary": summary,
            "brazilian_translation": translation
        }
    
    except Exception as e:
        return {"error": str(e)}
