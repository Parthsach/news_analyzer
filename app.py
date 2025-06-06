from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from model_utils import classify_news, summarize_news, interpret_news
from url_utils import extract_text_from_url
from news_verification import get_top_headlines, verify_news_topic, analyze_news_credibility
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

def format_news_analysis(output):
    # Extract all required data
    classification = output["classification"]
    labels = classification["labels"]
    scores = classification["scores"]
    percentages = [round(score * 100, 1) for score in scores]
    
    # Get the highest scoring classification
    max_score_index = scores.index(max(scores))
    primary_classification = labels[max_score_index]
    primary_score = percentages[max_score_index]

    # Summary and interpretation
    summary = output["summary"]
    interpretation = output["interpretation"]
    
    # Credibility analysis
    credibility = output["credibility_analysis"]
    credibility_score = round(credibility["credibility_score"] * 100, 1)
    assessment = credibility["assessment"]
    message = credibility["message"]
    
    # Related Articles
    related_articles = credibility["verification_results"].get("related_articles", [])
    
    # Build the formatted output sections
    header = "📰 NEWS ANALYSIS REPORT 📰"
    
    classification_section = (
        "🎯 CLASSIFICATION\n"
        f"Primary Category: {primary_classification.upper()} ({primary_score}%)\n"
        "\nDetailed Breakdown:\n"
        f"▪️ Factual: {percentages[1]}%\n"
        f"▪️ Opinionated: {percentages[0]}%\n"
        f"▪️ Biased: {percentages[2]}%\n"
        f"▪️ Potential Fake: {percentages[3]}%"
    )
    
    content_section = (
        "📝 CONTENT ANALYSIS\n"
        f"Summary:\n{summary}\n\n"
        f"Key Points:\n{interpretation}"
    )
    
    credibility_section = (
        "✅ CREDIBILITY CHECK\n"
        f"Trust Score: {credibility_score}%\n"
        f"Status: {assessment.upper()}\n"
        f"Analysis: {message}"
    )
    
    sources_section = "🔍 VERIFICATION SOURCES\n"
    if related_articles:
        sources_section += "Found Related Articles:\n"
        for idx, article in enumerate(related_articles, 1):
            sources_section += (
                f"{idx}. {article['title']}\n"
                f"   Source: {article['source']}\n"
                f"   Link: {article['url']}\n"
            )
    else:
        sources_section += "No matching articles found in current news"
    
    # Combine all sections with proper spacing
    result = (
        f"{header}\n\n"
        f"{classification_section}\n\n"
        f"{content_section}\n\n"
        f"{credibility_section}\n\n"
        f"{sources_section}"
    )
    
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

@app.post("/top-headlines")
async def get_headlines(req: TopHeadlinesRequest):
    """
    Get top headlines based on country and category
    """
    result = get_top_headlines(
        country=req.country,
        category=req.category,
        page=req.page,
        page_size=req.page_size
    )
    
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.post("/verify-topic")
async def verify_topic(topic: str, country: str = "in"):
    """
    Verify a news topic against current headlines
    """
    result = verify_news_topic(topic, country)
    
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
