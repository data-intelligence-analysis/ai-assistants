####Invoking Sagemaker Endpoints


##AWS Lambda for serverless execution. 
##Amazon S3 for storing the PDF documents.
##Amazon SageMaker for machine learning model training and inference. 
##Amazon DynamoDB for storing analysis results.

## Tech Arch Diagram: S3 -> Sagemaker <-> Lambda -> Dynamodb


#1. Lambda Function: This function will be triggered when a new PDF document is uploaded to an S3 bucket. It will orchestrate the analysis process by invoking SageMaker endpoints for anomaly detection, fraud detection, text classification (neural network), and NLP tasks. Finally, it will store the results in DynamoDB and return them to the front-end.

#2. SageMaker Models: You need to train and deploy machine learning models for anomaly detection, fraud detection, text classification (neural network), and NLP tasks using SageMaker.

#3. Front-end Web App: Develop a ReactJS web app dashboard to interact with users. This app will allow users to upload PDF documents and display the analysis results retrieved from DynamoDB.

#4. Amazon S3: Store the PDF documents in an S3 bucket. Configure the bucket to trigger the Lambda function when a new object is uploaded.

#5. Amazon DynamoDB: Create a DynamoDB table to store the analysis results.

#6. Make sure to properly configure the IAM roles for your Lambda function to have permissions to invoke SageMaker endpoints, access S3 buckets, and write to DynamoDB tables.

#7. On the front-end side, you can use AWS SDK or API Gateway to communicate with the Lambda function and display the analysis results in your ReactJS web app dashboard.

##### Lambda function #####

import boto3
import json
import os

sagemaker_runtime = boto3.client('sagemaker-runtime')
dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context): #Triggered by S3 events when new PDF documents are uploaded. It invokes SageMaker endpoints for anomaly detection, fraud detection, text classification, and NLP tasks. It then stores the results in DynamoDB and returns them to the front-end.
    # Extract information from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']
    # Invoke SageMaker endpoints for analysis - This helper function invokes a specific SageMaker endpoint for analysis and returns the result
    #replace 'anomaly_detection', 'fraud_detection', 'text_classification', and 'nlp' with the actual names of your SageMaker endpoints.
    anomaly_result = invoke_sagemaker_endpoint('anomaly_detection', bucket_name, file_key)
    fraud_detection_result = invoke_sagemaker_endpoint('fraud_detection', bucket_name, file_key)
    classification_result = invoke_sagemaker_endpoint('text_classification', bucket_name, file_key)
    nlp_result = invoke_sagemaker_endpoint('nlp', bucket_name, file_key)
    # Store results in DynamoDB
    dynamodb.put_item(
        TableName='analysis_results',
        Item={
            'file_key': {'S': file_key},
            'anomaly_result': {'S': anomaly_result},
            'fraud_detection_result': {'S': fraud_detection_result},
            'classification_result': {'S': classification_result},
            'nlp_result': {'S': nlp_result}
        }
    )
    
    # Return results to the front-end
    return {
        'statusCode': 200,
        'body': json.dumps({
            'anomaly_result': anomaly_result,
            'fraud_detection_result': fraud_detection_result,
            'classification_result': classification_result,
            'nlp_result': nlp_result
        })
    }

def invoke_sagemaker_endpoint(endpoint_name, bucket_name, file_key):
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        Body=bucket_name + '/' + file_key,
        ContentType='text/plain',
        Accept='application/json'
    )
    result = json.loads(response['Body'].read().decode())
    return result['result']