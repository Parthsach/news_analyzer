from fastapi import FastAPI
from pydantic import BaseModel
from model_utils import classify_news, summarize_news, interpret_news
from url_utils import extract_text_from_url

app = FastAPI()

class NewsRequest(BaseModel):
    text: str

class NewsURLRequest(BaseModel):
    url: str

@app.post("/analyze")
def analyze_news(req: NewsRequest):
    classification = classify_news(req.text)
    summary = summarize_news(req.text)
    return {
        "classification": classification,
        "summary": summary
    }

@app.post("/interpret")
def interpret_text(req: NewsRequest):
    result = interpret_news(req.text)
    return {"analysis": result}


@app.post("/interpret-from-url")
def interpret_from_url(req: NewsURLRequest):
    text = extract_text_from_url(req.url)
    result = interpret_news(text)
    return {"analysis": result}
