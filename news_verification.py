import os
import tweepy
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional
from sentence_transformers import SentenceTransformer, util
from source_credibility import SOURCE_CREDIBILITY
from urllib.parse import urlparse
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from twitter_utils import get_social_signals


sentiment_analyzer = SentimentIntensityAnalyzer()


load_dotenv()


# News API setup
WORLD_NEWS_API_KEY = "32519525455b4abf89df7850efd42ed3"  # World News API key

def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment using VADER.
    Returns compound score (-1 to 1) and classification.
    """
    scores = sentiment_analyzer.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        sentiment = 'Positive'
    elif compound <= -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'
    return {"compound_score": round(compound, 2), "sentiment": sentiment}



def search_news(query: str, offset: int = 0, number: int = 10, language: str = "en"):
    """
    Search news articles using the World News API search endpoint
    """
    try:
        base_url = "https://api.worldnewsapi.com/search-news"
        
        params = {
            "api-key": WORLD_NEWS_API_KEY,
            "text": query,
            "offset": offset,
            "number": number,
            "language": language
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200 and "news" in data:
            return {
                "status": "success",
                "total_results": data.get("available", 0),
                "articles": [{
                    "title": article.get("title", "No title"),
                    "description": article.get("text", "No description available"),
                    "source": article.get("source") or article.get("author", "unknown"),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("publish_date", "Unknown date"),
                    "content": article.get("text", "Full content not available"),
                    "sentiment": analyze_sentiment(article.get("text", ""))
                } for article in data.get("news", [])]
            }
        else:
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

def extract_domain(url: str) -> str:
    """
    Extracts the domain from a URL.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace("www.", "")
        return domain.lower()
    except Exception:
        return "unknown"

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def verify_news_topic(topic: str, days_back: int = 7, similarity_threshold: float = 0.5):
    """
    Verify a news topic against current and recent news using semantic similarity and source credibility.
    """
    try:
        search_results = search_news(topic)  # Removed days_back because your current search_news() doesn’t use it

        if search_results["status"] != "success":
            return {
                "status": "error",
                "message": "Could not verify against news sources"
            }

        articles = search_results["articles"]
        total_matches = len(articles)

        topic_embedding = embedding_model.encode(topic, convert_to_tensor=True)

        relevant_articles = []
        source_scores = []

        for article in articles:
            text = f"{article.get('title', '')}. {article.get('description', '')}"
            article_embedding = embedding_model.encode(text, convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(topic_embedding, article_embedding).item()

            domain = extract_domain(article.get('url', 'unknown'))
            credibility = SOURCE_CREDIBILITY.get(domain, 0.5)  # Default to 0.5 if unknown
            source_scores.append(credibility)

            sentiment = analyze_sentiment(text)

            if similarity >= similarity_threshold:
                relevant_articles.append({
                    "title": article["title"],
                    "source": article.get("source") or article.get("author") or domain,
                    "url": article["url"],
                    "published_at": article["publishedAt"],
                    "description": article.get("description", ""),
                    "similarity_score": round(similarity, 2),
                    "source_credibility": credibility,
                    "sentiment": sentiment,
                    "relevance": "High" if similarity > 0.7 else "Medium"
                })

        avg_source_credibility = round(sum(source_scores) / len(source_scores), 2) if source_scores else 0.5

        # Now get social signals from Twitter for the same topic
        social_signals = get_social_signals(topic)

        # Calculate social score from tweets (likes + retweets), normalize roughly to 0-1 scale
        social_score = 0
        if social_signals.get("status") == "success":
            tweets = social_signals.get("tweets", [])
            social_engagement = sum(tweet["likes"] + tweet["retweets"] for tweet in tweets[:10])  # top 10 tweets
            social_score = min(social_engagement / 500, 1.0)  # Example normalization factor

        # Combine news credibility and social score (weights can be adjusted)
        combined_score = 0.7 * avg_source_credibility + 0.3 * social_score

        # Final assessment based on combined score
        if combined_score >= 0.7:
            assessment = "highly verified"
        elif combined_score >= 0.4:
            assessment = "partially verified"
        else:
            assessment = "unverified"

        return {
             "status": "success",
             "found_matches": len(relevant_articles) > 0,
             "related_articles": sorted(relevant_articles, key=lambda x: x["similarity_score"], reverse=True)[:5],
             "total_matches": total_matches,
             "relevant_matches": len(relevant_articles),
             "avg_source_credibility": avg_source_credibility,
             "social_signals": social_signals,
             "social_score": round(social_score, 2),
             "combined_score": round(combined_score, 2),
             "assessment": assessment
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during verification: {str(e)}"
        }

def analyze_news_credibility(text: str, topic: str):
    """
    Analyze news credibility by comparing with current and recent news
    """
    # Get verification from news sources
    verification = verify_news_topic(topic)
    
    if verification["status"] == "success":
        # Calculate credibility score based on matches and relevance
        relevant_matches = verification.get("relevant_matches", 0)
        total_matches = verification.get("total_matches", 0)
        
        # Score calculation factors in both relevant and total matches
        base_score = min(relevant_matches * 0.2, 0.7)  # Up to 70% from relevant matches
        total_score = min(total_matches * 0.01, 0.3)   # Up to 30% from total matches
        credibility_score = min(base_score + total_score, 1.0)
        
        # Determine assessment based on score
        if credibility_score >= 0.7:
            assessment = "highly verified"
            message = "Topic widely covered by multiple reliable sources"
        elif credibility_score >= 0.4:
            assessment = "partially verified"
            message = "Topic found in some reliable sources"
        else:
            assessment = "unverified"
            message = "Limited or no coverage found in reliable sources"
        
        return {
            "credibility_score": credibility_score,
            "verification_results": verification,
            "assessment": assessment,
            "message": message
        }
    
    return {
        "status": "error",
        "message": verification["message"]
    }

def get_comprehensive_analysis(topic, text):
    """
    Get comprehensive analysis including related tweets and news verification
    """
    news_verification = verify_news_topic(topic)
    social_signals = get_social_signals(topic)
    
    return {
        "topic": topic,
        "news_verification": news_verification,
        "social_signals": social_signals
    }