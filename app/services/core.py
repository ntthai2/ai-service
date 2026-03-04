def load_model():
    pass

def predict_text(text: str):
    from textblob import TextBlob
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        label = "POSITIVE"
    else:
        label = "NEGATIVE"
    score = abs(polarity)
    return label, score
