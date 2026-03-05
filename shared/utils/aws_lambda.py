"""
AWS Lambda Integration Utilities for SarvaSahay Platform

This module provides utilities for invoking AWS Lambda functions
for serverless processing of eligibility checks, document processing,
and notifications.
"""

import json
import os
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError


class LambdaClient:
    """Client for invoking AWS Lambda functions"""
    
    def __init__(self):
        """Initialize Lambda client with AWS credentials from environment"""
        self.region = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')
        
        # Build client configuration
        client_config = {
            'region_name': self.region,
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
        }
        
        # Add custom endpoint URL if specified (for LocalStack or custom endpoints)
        endpoint_url = os.getenv('AWS_LAMBDA_ENDPOINT_URL')
        if endpoint_url:
            client_config['endpoint_url'] = endpoint_url
        
        self.lambda_client = boto3.client('lambda', **client_config)
        
        # Lambda function names from environment
        self.functions = {
            'eligibility': os.getenv('AWS_LAMBDA_ELIGIBILITY_FUNCTION', 'sarvasahay-eligibility-engine'),
            'document_processor': os.getenv('AWS_LAMBDA_DOCUMENT_PROCESSOR', 'sarvasahay-document-processor'),
            'ocr': os.getenv('AWS_LAMBDA_OCR_FUNCTION', 'sarvasahay-ocr-processor'),
            'notification': os.getenv('AWS_LAMBDA_NOTIFICATION_FUNCTION', 'sarvasahay-notification-handler'),
            'tracking': os.getenv('AWS_LAMBDA_TRACKING_FUNCTION', 'sarvasahay-tracking-updater')
        }
    
    def invoke_eligibility_engine(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke eligibility engine Lambda function
        
        Args:
            user_profile: User profile data for eligibility evaluation
            
        Returns:
            Dict containing eligible schemes and rankings
        """
        return self._invoke_lambda(
            function_name=self.functions['eligibility'],
            payload={'user_profile': user_profile},
            invocation_type='RequestResponse'
        )
    
    def invoke_document_processor(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke document processor Lambda function
        
        Args:
            document_data: Document information including S3 location
            
        Returns:
            Dict containing extracted document data
        """
        return self._invoke_lambda(
            function_name=self.functions['document_processor'],
            payload={'document': document_data},
            invocation_type='RequestResponse'
        )
    
    def invoke_ocr_processor(self, image_s3_key: str) -> Dict[str, Any]:
        """
        Invoke OCR processor Lambda function
        
        Args:
            image_s3_key: S3 key of the document image
            
        Returns:
            Dict containing OCR extracted text
        """
        return self._invoke_lambda(
            function_name=self.functions['ocr'],
            payload={'s3_key': image_s3_key},
            invocation_type='RequestResponse'
        )
    
    def invoke_notification_handler(
        self, 
        user_id: str, 
        notification_type: str, 
        message: str,
        async_invoke: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke notification handler Lambda function
        
        Args:
            user_id: User identifier
            notification_type: Type of notification (sms, voice, push)
            message: Notification message content
            async_invoke: Whether to invoke asynchronously
            
        Returns:
            Dict containing response if synchronous, None if async
        """
        invocation_type = 'Event' if async_invoke else 'RequestResponse'
        
        return self._invoke_lambda(
            function_name=self.functions['notification'],
            payload={
                'user_id': user_id,
                'type': notification_type,
                'message': message
            },
            invocation_type=invocation_type
        )
    
    def invoke_tracking_updater(
        self, 
        application_id: str,
        async_invoke: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke tracking updater Lambda function
        
        Args:
            application_id: Application identifier to track
            async_invoke: Whether to invoke asynchronously
            
        Returns:
            Dict containing tracking status if synchronous, None if async
        """
        invocation_type = 'Event' if async_invoke else 'RequestResponse'
        
        return self._invoke_lambda(
            function_name=self.functions['tracking'],
            payload={'application_id': application_id},
            invocation_type=invocation_type
        )
    
    def _invoke_lambda(
        self,
        function_name: str,
        payload: Dict[str, Any],
        invocation_type: str = 'RequestResponse'
    ) -> Optional[Dict[str, Any]]:
        """
        Internal method to invoke Lambda function
        
        Args:
            function_name: Name of Lambda function
            payload: Payload to send to function
            invocation_type: 'RequestResponse' (sync) or 'Event' (async)
            
        Returns:
            Response from Lambda if synchronous, None if async
            
        Raises:
            ClientError: If Lambda invocation fails
        """
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )
            
            # For async invocations, return None
            if invocation_type == 'Event':
                return None
            
            # For sync invocations, parse and return response
            response_payload = json.loads(response['Payload'].read())
            
            # Check for Lambda function errors
            if 'errorMessage' in response_payload:
                raise Exception(f"Lambda error: {response_payload['errorMessage']}")
            
            return response_payload
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise Exception(f"Lambda invocation failed [{error_code}]: {error_message}")


# Singleton instance
_lambda_client = None

def get_lambda_client() -> LambdaClient:
    """Get singleton Lambda client instance"""
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = LambdaClient()
    return _lambda_client
