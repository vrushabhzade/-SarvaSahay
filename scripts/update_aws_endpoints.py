#!/usr/bin/env python3
"""
AWS Endpoint Update Script for SarvaSahay Platform

This script helps update AWS endpoints across the platform configuration.
"""

import os
import re
import sys
from typing import Dict, Optional


class AWSEndpointUpdater:
    """Update AWS endpoints in configuration files"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load current configuration from .env file"""
        if not os.path.exists(self.env_file):
            print(f"Error: {self.env_file} not found")
            print("Please copy .env.example to .env first")
            sys.exit(1)
        
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    self.config[key] = value
    
    def update_region(self, new_region: str):
        """Update AWS region across all configurations"""
        print(f"\n🌍 Updating AWS region to: {new_region}")
        
        old_region = self.config.get('AWS_DEFAULT_REGION', 'ap-south-1')
        account_id = self.config.get('AWS_ACCOUNT_ID', 'ACCOUNT_ID')
        
        updates = {
            'AWS_DEFAULT_REGION': new_region,
        }
        
        # Update API Gateway endpoint
        if 'AWS_API_GATEWAY_ENDPOINT' in self.config:
            old_endpoint = self.config['AWS_API_GATEWAY_ENDPOINT']
            new_endpoint = old_endpoint.replace(old_region, new_region)
            updates['AWS_API_GATEWAY_ENDPOINT'] = new_endpoint
            print(f"  ✓ API Gateway: {new_endpoint}")
        
        # Update SNS topics
        sns_topics = [
            'AWS_SNS_TOPIC_ELIGIBILITY',
            'AWS_SNS_TOPIC_APPLICATIONS',
            'AWS_SNS_TOPIC_ALERTS'
        ]
        for topic in sns_topics:
            if topic in self.config:
                old_arn = self.config[topic]
                new_arn = old_arn.replace(old_region, new_region)
                updates[topic] = new_arn
                print(f"  ✓ SNS Topic: {new_arn}")
        
        # Update SQS queues
        sqs_queues = [
            'AWS_SQS_QUEUE_DOCUMENTS',
            'AWS_SQS_QUEUE_ELIGIBILITY',
            'AWS_SQS_QUEUE_NOTIFICATIONS'
        ]
        for queue in sqs_queues:
            if queue in self.config:
                old_url = self.config[queue]
                new_url = old_url.replace(old_region, new_region)
                updates[queue] = new_url
                print(f"  ✓ SQS Queue: {new_url}")
        
        self._apply_updates(updates)
        print(f"\n✅ Region updated successfully!")
    
    def update_api_gateway(self, api_id: str, region: Optional[str] = None):
        """Update API Gateway endpoint"""
        if region is None:
            region = self.config.get('AWS_DEFAULT_REGION', 'ap-south-1')
        
        stage = self.config.get('AWS_API_GATEWAY_STAGE', 'prod')
        endpoint = f"https://{api_id}.execute-api.{region}.amazonaws.com"
        
        print(f"\n🔗 Updating API Gateway endpoint:")
        print(f"  API ID: {api_id}")
        print(f"  Region: {region}")
        print(f"  Stage: {stage}")
        print(f"  Endpoint: {endpoint}")
        
        self._apply_updates({
            'AWS_API_GATEWAY_ENDPOINT': endpoint
        })
        
        print(f"\n✅ API Gateway endpoint updated!")
    
    def update_s3_buckets(self, documents: str, ml_models: str, backups: str):
        """Update S3 bucket names"""
        print(f"\n🪣 Updating S3 buckets:")
        print(f"  Documents: {documents}")
        print(f"  ML Models: {ml_models}")
        print(f"  Backups: {backups}")
        
        self._apply_updates({
            'AWS_S3_BUCKET_DOCUMENTS': documents,
            'AWS_S3_BUCKET_ML_MODELS': ml_models,
            'AWS_S3_BUCKET_BACKUPS': backups
        })
        
        print(f"\n✅ S3 buckets updated!")
    
    def update_lambda_functions(self, functions: Dict[str, str]):
        """Update Lambda function names"""
        print(f"\n⚡ Updating Lambda functions:")
        
        updates = {}
        for key, value in functions.items():
            env_key = f"AWS_LAMBDA_{key.upper()}_FUNCTION"
            updates[env_key] = value
            print(f"  {key}: {value}")
        
        self._apply_updates(updates)
        print(f"\n✅ Lambda functions updated!")
    
    def enable_localstack(self, localstack_url: str = "http://localhost:4566"):
        """Configure endpoints for LocalStack"""
        print(f"\n🐳 Configuring for LocalStack: {localstack_url}")
        
        updates = {
            'AWS_S3_ENDPOINT_URL': localstack_url,
            'AWS_LAMBDA_ENDPOINT_URL': localstack_url,
            'AWS_DYNAMODB_ENDPOINT_URL': localstack_url,
            'AWS_SQS_ENDPOINT_URL': localstack_url,
            'AWS_SNS_ENDPOINT_URL': localstack_url,
            'AWS_DEFAULT_REGION': 'us-east-1'
        }
        
        self._apply_updates(updates)
        print(f"\n✅ LocalStack configuration applied!")
        print(f"\n⚠️  Make sure LocalStack is running:")
        print(f"   docker run -d -p 4566:4566 localstack/localstack")
    
    def disable_localstack(self):
        """Remove LocalStack endpoint configurations"""
        print(f"\n🔄 Removing LocalStack configuration...")
        
        # Read current .env
        with open(self.env_file, 'r') as f:
            lines = f.readlines()
        
        # Remove LocalStack endpoint lines
        localstack_keys = [
            'AWS_S3_ENDPOINT_URL',
            'AWS_LAMBDA_ENDPOINT_URL',
            'AWS_DYNAMODB_ENDPOINT_URL',
            'AWS_SQS_ENDPOINT_URL',
            'AWS_SNS_ENDPOINT_URL'
        ]
        
        filtered_lines = []
        for line in lines:
            if not any(key in line for key in localstack_keys):
                filtered_lines.append(line)
        
        # Write back
        with open(self.env_file, 'w') as f:
            f.writelines(filtered_lines)
        
        print(f"\n✅ LocalStack configuration removed!")
    
    def _apply_updates(self, updates: Dict[str, str]):
        """Apply updates to .env file"""
        # Read current file
        with open(self.env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add lines
        updated_keys = set()
        new_lines = []
        
        for line in lines:
            updated = False
            for key, value in updates.items():
                if line.startswith(f"{key}="):
                    new_lines.append(f"{key}={value}\n")
                    updated_keys.add(key)
                    updated = True
                    break
            
            if not updated:
                new_lines.append(line)
        
        # Add new keys that weren't in the file
        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")
        
        # Write back
        with open(self.env_file, 'w') as f:
            f.writelines(new_lines)
    
    def show_current_config(self):
        """Display current AWS configuration"""
        print("\n📋 Current AWS Configuration:")
        print(f"\n  Region: {self.config.get('AWS_DEFAULT_REGION', 'Not set')}")
        print(f"  Account ID: {self.config.get('AWS_ACCOUNT_ID', 'Not set')}")
        
        print(f"\n  API Gateway:")
        print(f"    Endpoint: {self.config.get('AWS_API_GATEWAY_ENDPOINT', 'Not set')}")
        print(f"    Stage: {self.config.get('AWS_API_GATEWAY_STAGE', 'Not set')}")
        
        print(f"\n  S3 Buckets:")
        print(f"    Documents: {self.config.get('AWS_S3_BUCKET_DOCUMENTS', 'Not set')}")
        print(f"    ML Models: {self.config.get('AWS_S3_BUCKET_ML_MODELS', 'Not set')}")
        print(f"    Backups: {self.config.get('AWS_S3_BUCKET_BACKUPS', 'Not set')}")
        
        print(f"\n  Lambda Functions:")
        print(f"    Eligibility: {self.config.get('AWS_LAMBDA_ELIGIBILITY_FUNCTION', 'Not set')}")
        print(f"    Document Processor: {self.config.get('AWS_LAMBDA_DOCUMENT_PROCESSOR', 'Not set')}")
        print(f"    OCR: {self.config.get('AWS_LAMBDA_OCR_FUNCTION', 'Not set')}")
        
        # Check for LocalStack
        if 'AWS_S3_ENDPOINT_URL' in self.config:
            print(f"\n  🐳 LocalStack Enabled:")
            print(f"    Endpoint: {self.config.get('AWS_S3_ENDPOINT_URL')}")


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update AWS endpoints for SarvaSahay Platform'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Show current config
    subparsers.add_parser('show', help='Show current AWS configuration')
    
    # Update region
    region_parser = subparsers.add_parser('region', help='Update AWS region')
    region_parser.add_argument('new_region', help='New AWS region (e.g., us-east-1)')
    
    # Update API Gateway
    api_parser = subparsers.add_parser('api-gateway', help='Update API Gateway endpoint')
    api_parser.add_argument('api_id', help='API Gateway ID')
    api_parser.add_argument('--region', help='AWS region (optional)')
    
    # Update S3 buckets
    s3_parser = subparsers.add_parser('s3', help='Update S3 bucket names')
    s3_parser.add_argument('--documents', required=True, help='Documents bucket name')
    s3_parser.add_argument('--ml-models', required=True, help='ML models bucket name')
    s3_parser.add_argument('--backups', required=True, help='Backups bucket name')
    
    # LocalStack
    localstack_parser = subparsers.add_parser('localstack', help='Configure LocalStack')
    localstack_parser.add_argument('--enable', action='store_true', help='Enable LocalStack')
    localstack_parser.add_argument('--disable', action='store_true', help='Disable LocalStack')
    localstack_parser.add_argument('--url', default='http://localhost:4566', help='LocalStack URL')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    updater = AWSEndpointUpdater()
    
    if args.command == 'show':
        updater.show_current_config()
    
    elif args.command == 'region':
        updater.update_region(args.new_region)
    
    elif args.command == 'api-gateway':
        updater.update_api_gateway(args.api_id, args.region)
    
    elif args.command == 's3':
        updater.update_s3_buckets(args.documents, args.ml_models, args.backups)
    
    elif args.command == 'localstack':
        if args.enable:
            updater.enable_localstack(args.url)
        elif args.disable:
            updater.disable_localstack()
        else:
            print("Please specify --enable or --disable")
    
    print(f"\n💡 Tip: Restart services for changes to take effect:")
    print(f"   docker-compose down && docker-compose up -d\n")


if __name__ == '__main__':
    main()
