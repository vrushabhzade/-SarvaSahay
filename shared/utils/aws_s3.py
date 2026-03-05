"""
AWS S3 Integration Utilities for SarvaSahay Platform

This module provides utilities for uploading, downloading, and managing
documents in AWS S3 buckets.
"""

import os
from typing import Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError


class S3Client:
    """Client for AWS S3 operations"""
    
    def __init__(self):
        """Initialize S3 client with AWS credentials from environment"""
        self.region = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')
        
        # Build client configuration
        client_config = {
            'region_name': self.region,
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
        }
        
        # Add custom endpoint URL if specified (for LocalStack or custom endpoints)
        endpoint_url = os.getenv('AWS_S3_ENDPOINT_URL')
        if endpoint_url:
            client_config['endpoint_url'] = endpoint_url
        
        self.s3_client = boto3.client('s3', **client_config)
        
        # S3 bucket names from environment
        self.buckets = {
            'documents': os.getenv('AWS_S3_BUCKET_DOCUMENTS', 'sarvasahay-documents'),
            'ml_models': os.getenv('AWS_S3_BUCKET_ML_MODELS', 'sarvasahay-ml-models'),
            'backups': os.getenv('AWS_S3_BUCKET_BACKUPS', 'sarvasahay-backups')
        }
    
    def upload_document(
        self, 
        file_obj: BinaryIO, 
        user_id: str, 
        document_type: str,
        file_extension: str = 'jpg'
    ) -> str:
        """
        Upload document to S3
        
        Args:
            file_obj: File object to upload
            user_id: User identifier
            document_type: Type of document (aadhaar, pan, etc.)
            file_extension: File extension
            
        Returns:
            S3 key of uploaded file
        """
        s3_key = f"documents/{user_id}/{document_type}.{file_extension}"
        
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.buckets['documents'],
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'ContentType': f'image/{file_extension}'
                }
            )
            return s3_key
        except ClientError as e:
            raise Exception(f"Failed to upload document: {e}")
    
    def download_document(self, s3_key: str) -> bytes:
        """
        Download document from S3
        
        Args:
            s3_key: S3 key of the document
            
        Returns:
            Document content as bytes
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.buckets['documents'],
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Failed to download document: {e}")
    
    def delete_document(self, s3_key: str) -> bool:
        """
        Delete document from S3
        
        Args:
            s3_key: S3 key of the document
            
        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.buckets['documents'],
                Key=s3_key
            )
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete document: {e}")
    
    def generate_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for document access
        
        Args:
            s3_key: S3 key of the document
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.buckets['documents'],
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")
    
    def upload_ml_model(self, model_path: str, model_version: str) -> str:
        """
        Upload ML model to S3
        
        Args:
            model_path: Local path to model file
            model_version: Version identifier for the model
            
        Returns:
            S3 key of uploaded model
        """
        s3_key = f"models/eligibility/{model_version}/model.pkl"
        
        try:
            self.s3_client.upload_file(
                model_path,
                self.buckets['ml_models'],
                s3_key,
                ExtraArgs={'ServerSideEncryption': 'AES256'}
            )
            return s3_key
        except ClientError as e:
            raise Exception(f"Failed to upload ML model: {e}")


# Singleton instance
_s3_client = None

def get_s3_client() -> S3Client:
    """Get singleton S3 client instance"""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
