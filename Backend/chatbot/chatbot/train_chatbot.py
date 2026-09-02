"""
Trains a simple intent-classification model for the chatbot.

Run this once (and again any time you edit training_data.py):
    python train_chatbot.py

Produces two files in this folder:
    chatbot_model.pkl      - the trained classifier
    vectorizer.pkl         - converts text into numbers the model understands
"""

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from training_data import TRAINING_DATA

texts = [t for t, _ in TRAINING_DATA]
labels = [l for _, l in TRAINING_DATA]

print(f"Training on {len(texts)} examples across {len(set(labels))} intents...")

vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
X = vectorizer.fit_transform(texts)

X_train, X_test, y_train, y_test = train_test_split(
    X, labels, test_size=0.2, random_state=42, stratify=labels
)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

print("\n--- Evaluation on held-out examples ---")
predictions = model.predict(X_test)
print(classification_report(y_test, predictions, zero_division=0))

model.fit(X, labels)

joblib.dump(model, "chatbot_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("\nSaved chatbot_model.pkl and vectorizer.pkl in this folder.")
print("Restart your Flask backend to load the newly trained model.")