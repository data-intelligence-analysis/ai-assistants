### Lambda Function

###Resources###
##Amazon SageMaker for model training and inference
##AWS Lambda for orchestrating the analysis process
##Amazon S3 for storage. The results can be stored in Amazon DynamoDB and displayed on a ReactJS web app hosted on Amazon S3 or AWS Amplify.

#1. SageMaker Model Training: Train machine learning models for anomaly and fraud detection, neural network classification, NLP tasks, and OCR using SageMaker built-in algorithms or custom scripts.
#2. SageMaker Model Deployment: Deploy the trained models as SageMaker endpoints to perform inference.
#3. AWS Lambda Function: Write a Lambda function to orchestrate the analysis process. This function should trigger when a new PDF document is uploaded to an Amazon S3 bucket.
#4. PDF Processing: Extract text from the PDF using a library like PyPDF2 or Tesseract.
#5. Model Inference: Invoke the SageMaker endpoints to perform inference using the extracted text.
#6. Result Storage: Store the analysis results, including anomaly/fraud detection, classification, and NLP outputs, in Amazon DynamoDB.
#7. ReactJS Web App: Develop a ReactJS web app frontend to display the analysis results. Use AWS SDK or API Gateway to communicate with the Lambda function and DynamoDB.


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

def analyze_pdf(event, context):
    # Extract information from the event
    s3 = boto3.client('s3')
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']

    # Download PDF file from S3
    local_path = '/tmp/temp_pdf.pdf'
    s3.download_file(bucket_name, file_key, local_path)

    # Extract text from the PDF
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
    
    # Store results in DynamoDB
    dynamodb = boto3.client('dynamodb')
    table_name = 'analysis_results'
    response = dynamodb.put_item(
        TableName=table_name,
        Item={
            'file_key': {'S': file_key},
            'anomaly_result': {'S': str(anomaly_result)},
            'classification_result': {'S': str(classification_result)},
            'topic_modeling_result': {'S': str(topic_modeling_result)}
        }
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Analysis completed and results stored in DynamoDB.')
    }