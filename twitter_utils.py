import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_social_signals(topic: str, max_results: int = 20):
    """
    Fetch recent tweets as social signals for a given news topic.
    """
    try:
        BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAPg12QEAAAAAHOX6jdmlAfxihE26dPgi1gGWiZI%3DWL5mldDvLh310IuVAqRmP07NlRIhJBAhqbM4KdOHdtyTQrcUcl"
        if not BEARER_TOKEN:
            return {
                "status": "error",
                "message": "Twitter Bearer Token not found."
            }
        
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
        params = {
            "query": topic,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,text,author_id"
        }

        response = requests.get(search_url, headers=headers, params=params)
        data = response.json()
        
        if response.status_code == 200 and "data" in data:
            tweets = []
            for tweet in data["data"]:
                public_metrics = tweet.get("public_metrics", {})
                tweets.append({
                    "text": tweet.get("text", ""),
                    "likes": public_metrics.get("like_count", 0),
                    "retweets": public_metrics.get("retweet_count", 0),
                    "replies": public_metrics.get("reply_count", 0),
                    "created_at": tweet.get("created_at", ""),
                    "author_id": tweet.get("author_id", "")
                })
            
            return {
                "status": "success",
                "tweets": sorted(tweets, key=lambda x: (x["likes"] + x["retweets"]), reverse=True)
            }
        else:
            return {
                "status": "error",
                "message": data.get("detail", "Failed to fetch tweets.")
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching social signals: {str(e)}"
        }
