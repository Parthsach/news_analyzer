# fake_news_classifier.py

from transformers import pipeline

# Use a small, available model like "mrm8488/bert-tiny-finetuned-sms-spam-detection"
fake_news_classifier = pipeline(
    "text-classification",
    model="mrm8488/bert-tiny-finetuned-sms-spam-detection"
)

def classify_fake_news(text: str):
    """
    Classify news text as fake or real using a pre-trained model.
    """
    try:
        result = fake_news_classifier(text)
        label = result[0]['label']
        score = result[0]['score']

        # We'll interpret "spam" as "fake" and "ham" as "real" here for demonstration.
        classification = "fake" if label.lower() == "spam" else "real"
        confidence = round(score, 2)

        return {
            "status": "success",
            "classification": classification,
            "confidence": confidence
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
