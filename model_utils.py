from transformers import pipeline

# Load ML pipelines
zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
interpreter = pipeline("text2text-generation", model="google/flan-t5-base")

def classify_news(text):
    labels = ["biased", "factual", "opinionated", "fake"]
    result = zero_shot_classifier(text, labels)
    return {
        "labels": result["labels"],
        "scores": result["scores"]
    }

def summarize_news(text):
    summary = summarizer(text, max_length=100, min_length=30, do_sample=False)
    return summary[0]["summary_text"]

def interpret_news(text):
    prompt = f"""
    Analyze the tone, intent, and reliability of this news:\n"{text}"\n\n
    Format:\n
    - Tone: [Sarcastic / Neutral / Confusing / Emotional]\n
    - Intent: [Factual / Opinionated / Biased / Misleading]\n
    - Legitimacy: [Likely True / Likely Fake]\n
    - Summary: <short line>
    """
    result = interpreter(prompt, max_length=256, do_sample=False)
    return result[0]["generated_text"]
