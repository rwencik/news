import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Use zoneinfo for timezone support

# Third-party library imports
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import feedparser
from googletrans import Translator
from bs4 import BeautifulSoup
from transformers import pipeline, logging as transformers_logging

# Set logging verbosity for transformers to error
transformers_logging.set_verbosity_error()

# Logging setup
log_directory = "/app/logs"
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, "news_bot.log")

handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Translator setup
translator = Translator()

# Email configurations (replace with your credentials or load from environment)
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "your_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_email_password")
EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')

if isinstance(EMAIL_RECIPIENTS, str):
    EMAIL_RECIPIENTS = [EMAIL_RECIPIENTS]

RSS_FEED_URLS = os.getenv("RSS_FEED_URL", '["https://rss.jpost.com/rss/rssfeedsheadlines.aspx"]').strip('[]').replace('"', '').split(',')

def fetch_rss_news():
    """Fetch news articles from a list of RSS feeds."""
    logger.info("Fetching news from RSS feeds...")
    news_list = []

    for url in RSS_FEED_URLS:
        url = url.strip()
        logger.info(f"Fetching news from: {url}")
        feed = feedparser.parse(url)

        for entry in feed.entries:
            # Parse the published date and make it timezone-aware
            try:
                published = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
                published = published.replace(tzinfo=ZoneInfo("Asia/Jerusalem"))  # Assume RSS times are in UTC
            except (ValueError, AttributeError):
                logger.warning(f"Skipping entry with invalid date format: {entry.get('title', 'Unknown Title')}")
                continue

            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "published": published,
            })

    # Sort the news list by published date, descending
    news_list.sort(key=lambda x: x["published"], reverse=True)

    logger.info(f"Fetched {len(news_list)} articles from {len(RSS_FEED_URLS)} feeds.")
    return news_list

def summarize_text(text, max_summary_length=32):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    # Ensure text is not empty or None
    if not text or len(text.strip()) == 0:
        return "No content to summarize"

    # Adjust max_length dynamically based on the input length
    max_length = max(min(len(text.split()), max_summary_length), 10)  # Ensure at least 10 tokens
    min_length = max(5, max_length // 2)  # Ensure reasonable min length
    
    try:
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)[0]["summary_text"]
        return summary
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        return "Error generating summary"

def translate_text(texto):
    try:
        return translator.translate(texto, dest='pt').text
    except Exception as e:
        logger.error(f"Erro na tradução: {str(e)}")
        return texto

def fetch_article_content(url):
    """Fetch the relevant article content from the URL, avoiding repeated sections."""
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to load article page {url}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Locate the specific container for the article body
        article_body = soup.find('section', class_='article-inner-content-breaking-news')
        
        if not article_body:
            logger.warning(f"Could not find the article content for {url}")
            return None
        
        # Extract unique paragraphs
        seen = set()
        content = []
        
        for p in article_body.find_all('p', recursive=False):  # Only direct <p> tags within article body
            text = p.get_text(strip=True)
            normalized_text = text.lower().replace(' ', '')  # Normalize to detect duplicates
            if text and normalized_text not in seen:
                content.append(text)
                seen.add(normalized_text)
        
        # Combine unique paragraphs into a single string
        return "\n".join(content).strip()
    except Exception as e:
        logger.error(f"Error fetching content for {url}: {str(e)}")
        return None

def filter_news(news_list, start_time, end_time):
    """Filter news articles by the specified time range and fetch content."""
    logger.info(f"Filtering news between {start_time} and {end_time} (UTC)")
    print(f"Buscando notícias de {start_time.strftime('%d/%m às %H:%M')} até agora: {end_time.strftime('%d/%m às %H:%M')}")
    filtered_news = []

    for news in news_list:
        logger.info(f"Checking article: {news['title']} published at {news['published']}")
        if start_time <= news["published"] <= end_time:
            logger.info(f"Article is within the time range: {news['title']}")
            
            # Fetch and add the article content only for relevant news
            article_content = summarize_text(translate_text(fetch_article_content(news["link"])))
            news["content"] = article_content
            
            filtered_news.append(news)
        else:
            logger.info(f"Article is outside the time range: {news['title']}")

    logger.info(f"Filtered {len(filtered_news)} articles within the time range.")
    return filtered_news

def send_email(news_list):
    """Send an email with the news summary."""
    logger.info("Building and sending email...")

    if not news_list:
        logger.info("No news to send.")
        return

def send_email(news_list):
    """Send an email with the news summary."""
    logger.info("Building and sending email...")

    if not news_list:
        logger.info("No news to send.")
        return

    email_body = ""
    for news in news_list:
        # Translate the title
        title_translated = translate_text(news["title"])

        # Format the title with bold and date-time
        formatted_title = f"<b>{title_translated} - {news['published'].strftime('%d/%m %H:%M')}</b>"

        # Use content or fallback to the title for the summary
        summary = news.get("content") or title_translated

        # Append the title, summary, and link to the email body
        email_body += f"{formatted_title}<br>{summary}<br><a href='{news['link']}'>Ver mais</a><br><br>"

    # Build the email
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECIPIENTS)
    msg["Subject"] = "Últimas notícias - https://www.jpost.com"
    msg.attach(MIMEText(email_body, "html"))  # Set email content type to HTML

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            for email in EMAIL_RECIPIENTS:
                server.sendmail(EMAIL_SENDER, email, msg.as_string())
            logger.info("Email sent successfully!")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")

def main():
    """Main function to fetch, filter, and send news."""
    now = datetime.now(ZoneInfo("Asia/Jerusalem"))  # Current time in Jerusalem
    logger.info(f"Current local time in Jerusalem: {now}")

    # Define the time range for filtering news
    if now.hour >= 8 and now.hour < 20:  # If it's between 8 AM and 8 PM
        start_time = (now - timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0).astimezone(ZoneInfo("Asia/Jerusalem"))
    else:  # If it's between 8 PM and 8 AM
        start_time = now.replace(hour=8, minute=0, second=0, microsecond=0).astimezone(ZoneInfo("Asia/Jerusalem"))
    
    end_time = now.astimezone(ZoneInfo("Asia/Jerusalem"))  # Current time in UTC

    logger.info(f"Filtering news from {start_time} to {end_time} (UTC)")

    # Fetch news, filter by time range, and send email
    news_list = fetch_rss_news()
    relevant_news = filter_news(news_list, start_time, end_time)

    logger.info(f"Relevant news: {relevant_news}")
#    print(f"Relevant news: {relevant_news}")
    send_email(relevant_news)



if __name__ == "__main__":
    main()
