####Fraud and Anamoly Detection utilizing AWS Sagemaker Notebook###

##Main Code
import json
import boto3
import PyPDF2
import re
import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.ensemble import IsolationForest
from sklearn.neural_network import MLPClassifier
import pytesseract
from PIL import Image
import spacy

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

def preprocess_text(text):
    # Tokenization using spaCy
    doc = nlp(text)
    tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
    # Remove non-alphanumeric characters and convert to lowercase
    tokens = [re.sub(r'[^a-zA-Z0-9]', '', token).lower() for token in tokens]
    return ' '.join(tokens)

# Function for anomaly detection
def anomaly_detection(X):
    model = IsolationForest()
    model.fit(X)
    return model.predict(X)

# Function for text classification using neural network
def text_classification(X, y):
    model = MLPClassifier()
    model.fit(X, y)
    return model.predict(X)

# Function for topic modeling
def topic_modeling(X):
    vectorizer = TfidfVectorizer(stop_words='english')
    X_tfidf = vectorizer.fit_transform(X)
    lda = LatentDirichletAllocation(n_components=5, random_state=42)
    topics = lda.fit_transform(X_tfidf)
    return topics

# Load S3 client
s3 = boto3.client('s3')

def extract_text_from_pdf():
    #place code here for extraction
    pass

def perform_ocr():
    #place code here for extracting data from images
    pass

def analyze_pdf(pdf_key):
    # Download PDF from S3
    local_path = '/tmp/temp_pdf.pdf'
    s3.download_file('<your_bucket>', pdf_key, local_path)

    # Extract text from PDF
    text = extract_text_from_pdf(local_path)
    
    # Perform OCR
    ocr_text = perform_ocr(local_path)
    
    # Preprocess text
    preprocessed_text = preprocess_text(text)
    preprocessed_ocr_text = preprocess_text(ocr_text)
    
    # Combine text
    combined_text = preprocessed_text + ' ' + preprocessed_ocr_text
    
    # Anomaly detection
    X_anomaly = np.array([len(combined_text)])
    anomaly_result = anomaly_detection(X_anomaly)
    
    # Text classification
    X_classification = np.array([combined_text])
    # Dummy label for demonstration purpose
    y_classification = np.array([0])
    classification_result = text_classification(X_classification, y_classification)
    
    # Topic modeling
    X_topic_modeling = [preprocessed_text, preprocessed_ocr_text]
    topic_modeling_result = topic_modeling(X_topic_modeling)
    
    return anomaly_result, classification_result, topic_modeling_result

# Example usage
pdf_key = '<your_pdf_key_in_s3>'
anomaly_result, classification_result, topic_modeling_result = analyze_pdf(pdf_key)
print("Anomaly Detection Result:", anomaly_result)
print("Text Classification Result:", classification_result)
print("Topic Modeling Result:", topic_modeling_result)