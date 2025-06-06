from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, Query
from pydantic import BaseModel, HttpUrl
from model_utils import classify_news, summarize_news, interpret_news
from url_utils import extract_text_from_url
from news_verification import  verify_news_topic, analyze_news_credibility, search_news
from typing import Optional

app = FastAPI(title="News Analyzer & Verifier")

class NewsRequest(BaseModel):
    text: str
    topic: Optional[str] = None

class NewsURLRequest(BaseModel):
    url: HttpUrl
    topic: Optional[str] = None

class TopHeadlinesRequest(BaseModel):
    country: str = "in"
    category: Optional[str] = None
    page: int = 1
    page_size: int = 10

class NewsSearchRequest(BaseModel):
    query: str
    days_back: Optional[int] = 7
    sort_by: Optional[str] = "popularity"
    language: Optional[str] = "en"

def format_news_analysis(output):
    """
    Formats the news analysis output into a readable dictionary format.
    Handles missing keys like 'credibility_score' to prevent KeyErrors.
    """

    # 1️⃣ Classification block
    classification = output.get("classification", {})
    labels = classification.get("labels", [])
    scores = classification.get("scores", [])
    percentages = [round(score * 100, 1) for score in scores]

    # Identify the top classification if available
    if scores:
        max_score_index = scores.index(max(scores))
        primary_classification = labels[max_score_index]
        primary_score = percentages[max_score_index]
    else:
        primary_classification = "unknown"
        primary_score = 0

    # 2️⃣ Summary block
    summary = output.get("summary", "No summary available.")

    # 3️⃣ Interpretation block
    interpretation = output.get("interpretation", "No interpretation available.")

    # 4️⃣ Credibility Analysis block (with safe fallback handling)
    credibility = output.get("credibility_analysis", {})
    credibility_score = round(credibility.get("credibility_score", 0), 1)
    assessment = credibility.get("assessment", "unverified")
    credibility_message = credibility.get("message", "No credibility information available.")

    # 5️⃣ Combine everything into a result dictionary
    result = {
        "Classification": {
            "Labels": labels,
            "Percentages": percentages,
            "Primary Classification": primary_classification,
            "Primary Score (%)": primary_score
        },
        "Summary": summary,
        "Interpretation": interpretation,
        "Credibility Analysis": {
            "Score (%)": credibility_score,
            "Assessment": assessment,
            "Message": credibility_message
        }
    }

    return result



@app.post("/analyze")
def analyze_news(req: NewsRequest):
    """
    Analyze news text and provide classification, summary, and real-time verification
    """
    # Basic analysis
    classification = classify_news(req.text)
    summary = summarize_news(req.text)
    interpretation = interpret_news(req.text)
    
    # Get topic if not provided
    topic = req.topic if req.topic else ' '.join(summary.split()[:3])
    
    # Get credibility analysis
    credibility = analyze_news_credibility(req.text, topic)
    
    
    # Prepare raw output
    raw_output = {
        "classification": classification,
        "summary": summary,
        "interpretation": interpretation,
        "credibility_analysis": credibility
    }
    formatted_output = format_news_analysis(raw_output)

    return {
        "raw": raw_output,
        "formatted": formatted_output
    }

@app.post("/analyze-url")
async def analyze_from_url(req: NewsURLRequest):
    """
    Analyze news from URL and provide comprehensive analysis
    """
    try:
        text = extract_text_from_url(str(req.url))
        news_request = NewsRequest(text=text, topic=req.topic)
        return analyze_news(news_request)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing URL: {str(e)}")


@app.post("/verify-topic")
async def verify_topic(topic: str, days_back: int = 7):
    """
    Verify a news topic against current headlines
    """
    result = verify_news_topic(topic, days_back)
    
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.post("/interpret")
def interpret_text(req: NewsRequest):
    result = interpret_news(req.text)
    return {"analysis": result}


@app.post("/interpret-from-url")
def interpret_from_url(req: NewsURLRequest):
    text = extract_text_from_url(req.url)
    result = interpret_news(text)
    return {"analysis": result}

@app.get("/search-news")
def search_news_endpoint(
    query: str = Query(..., description="Search query"),
    offset: int = Query(0, description="Offset for pagination"),
    number: int = Query(10, description="Number of articles to fetch"),
    language: str = Query("en", description="Language of the news")
):
    result = search_news(query, offset=offset, number=number, language=language)
    return result
