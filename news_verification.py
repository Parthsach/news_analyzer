import os
import tweepy
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Twitter API setup
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET')

# News API setup
NEWS_API_KEY = "0be1445e84da4a9fa1c28780604c5c92"

def setup_twitter_client():
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    return tweepy.API(auth)

def get_related_tweets(topic, count=5):
    try:
        api = setup_twitter_client()
        tweets = api.search_tweets(q=topic, lang="en", count=count, tweet_mode="extended")
        return [{"text": tweet.full_text, "created_at": tweet.created_at} for tweet in tweets]
    except Exception as e:
        return {"error": f"Could not fetch tweets: {str(e)}"}

def get_top_headlines(country: str = "in", category: Optional[str] = None, page: int = 1, page_size: int = 10):
    """
    Get top headlines from News API
    """
    try:
        base_url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": country,
            "apiKey": NEWS_API_KEY,
            "page": page,
            "pageSize": page_size
        }
        
        if category:
            params["category"] = category
            
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if data.get("status") == "ok":
            return {
                "status": "success",
                "total_results": data.get("totalResults", 0),
                "articles": data.get("articles", [])
            }
        return {
            "status": "error",
            "message": "Failed to fetch news",
            "raw_response": data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def verify_news_topic(topic: str, country: str = "in"):
    """
    Verify a news topic against current headlines
    """
    try:
        # Get current headlines
        headlines = get_top_headlines(country=country, page_size=20)
        
        if headlines["status"] != "success":
            return {
                "status": "error",
                "message": "Could not verify against current headlines"
            }
            
        # Find related articles
        related_articles = []
        for article in headlines["articles"]:
            # Check if topic appears in title or description
            if (topic.lower() in article["title"].lower() or 
                (article.get("description") and topic.lower() in article["description"].lower())):
                related_articles.append({
                    "title": article["title"],
                    "source": article["source"]["name"],
                    "url": article["url"],
                    "published_at": article["publishedAt"],
                    "description": article.get("description", "")
                })
        
        return {
            "status": "success",
            "found_matches": len(related_articles) > 0,
            "related_articles": related_articles,
            "total_matches": len(related_articles)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during verification: {str(e)}"
        }

def analyze_news_credibility(text: str, topic: str):
    """
    Analyze news credibility by comparing with current headlines
    """
    # Get verification from current headlines
    verification = verify_news_topic(topic)
    
    # Determine credibility score based on matches
    if verification["status"] == "success":
        credibility_score = min(len(verification["related_articles"]) * 0.2, 1.0)  # 0.0 to 1.0
        
        return {
            "credibility_score": credibility_score,
            "verification_results": verification,
            "assessment": "verified" if credibility_score > 0.4 else "unverified",
            "message": (
                "News topic found in multiple current sources" if credibility_score > 0.7
                else "News topic found in some current sources" if credibility_score > 0.4
                else "News topic not found in current headlines"
            )
        }
    
    return {
        "status": "error",
        "message": verification["message"]
    }

def get_comprehensive_analysis(topic, text):
    """
    Get comprehensive analysis including related tweets and news verification
    """
    tweets = get_related_tweets(topic)
    news_verification = verify_news_topic(topic)
    
    return {
        "related_tweets": tweets,
        "news_verification": news_verification,
        "topic": topic
    } 