from transformers import pipeline

classifier = None

def load_model():
    global classifier
    classifier = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )

def predict_text(text: str):
    result = classifier(text)[0]
    return result["label"], float(result["score"])
