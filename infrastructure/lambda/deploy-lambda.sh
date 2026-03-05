#!/bin/bash
# AWS Lambda Deployment Script for SarvaSahay Platform
# This script packages and deploys Lambda functions to AWS

set -e

# Configuration
REGION=${AWS_DEFAULT_REGION:-ap-south-1}
ACCOUNT_ID=${AWS_ACCOUNT_ID}
PROJECT_NAME="sarvasahay"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SarvaSahay Lambda Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
aws sts get-caller-identity > /dev/null 2>&1 || {
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
}
echo -e "${GREEN}✓ AWS credentials verified${NC}"

# Function to package Lambda function
package_lambda() {
    local function_name=$1
    local source_dir=$2
    local output_file=$3
    
    echo -e "${YELLOW}Packaging ${function_name}...${NC}"
    
    # Create temporary directory
    temp_dir=$(mktemp -d)
    
    # Copy function code
    cp -r ${source_dir}/* ${temp_dir}/
    
    # Install dependencies
    if [ -f "${source_dir}/requirements.txt" ]; then
        pip install -r ${source_dir}/requirements.txt -t ${temp_dir}/ --quiet
    fi
    
    # Create zip file
    cd ${temp_dir}
    zip -r ${output_file} . > /dev/null
    cd -
    
    # Cleanup
    rm -rf ${temp_dir}
    
    echo -e "${GREEN}✓ Packaged ${function_name}${NC}"
}

# Function to deploy Lambda function
deploy_lambda() {
    local function_name=$1
    local zip_file=$2
    local handler=$3
    local runtime=$4
    local memory=$5
    local timeout=$6
    local role=$7
    
    echo -e "${YELLOW}Deploying ${function_name}...${NC}"
    
    # Check if function exists
    if aws lambda get-function --function-name ${function_name} --region ${REGION} > /dev/null 2>&1; then
        # Update existing function
        aws lambda update-function-code \
            --function-name ${function_name} \
            --zip-file fileb://${zip_file} \
            --region ${REGION} > /dev/null
        
        echo -e "${GREEN}✓ Updated ${function_name}${NC}"
    else
        # Create new function
        aws lambda create-function \
            --function-name ${function_name} \
            --runtime ${runtime} \
            --role ${role} \
            --handler ${handler} \
            --zip-file fileb://${zip_file} \
            --memory-size ${memory} \
            --timeout ${timeout} \
            --region ${REGION} \
            --tags Project=${PROJECT_NAME},Environment=production > /dev/null
        
        echo -e "${GREEN}✓ Created ${function_name}${NC}"
    fi
}

# Deploy Eligibility Engine Lambda
echo -e "\n${YELLOW}=== Deploying Eligibility Engine ===${NC}"
package_lambda \
    "eligibility-engine" \
    "services/eligibility_engine" \
    "/tmp/eligibility-engine.zip"

deploy_lambda \
    "${PROJECT_NAME}-eligibility-engine" \
    "/tmp/eligibility-engine.zip" \
    "lambda_function.lambda_handler" \
    "python3.11" \
    "3008" \
    "300" \
    "arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-eligibility-lambda-role"

# Deploy Document Processor Lambda
echo -e "\n${YELLOW}=== Deploying Document Processor ===${NC}"
package_lambda \
    "document-processor" \
    "services/document_processor" \
    "/tmp/document-processor.zip"

deploy_lambda \
    "${PROJECT_NAME}-document-processor" \
    "/tmp/document-processor.zip" \
    "lambda_function.lambda_handler" \
    "python3.11" \
    "2048" \
    "180" \
    "arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-document-lambda-role"

# Deploy OCR Processor Lambda
echo -e "\n${YELLOW}=== Deploying OCR Processor ===${NC}"
package_lambda \
    "ocr-processor" \
    "services/ocr_processor" \
    "/tmp/ocr-processor.zip"

deploy_lambda \
    "${PROJECT_NAME}-ocr-processor" \
    "/tmp/ocr-processor.zip" \
    "lambda_function.lambda_handler" \
    "python3.11" \
    "1536" \
    "120" \
    "arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-ocr-lambda-role"

# Deploy Notification Handler Lambda
echo -e "\n${YELLOW}=== Deploying Notification Handler ===${NC}"
package_lambda \
    "notification-handler" \
    "services/notification_handler" \
    "/tmp/notification-handler.zip"

deploy_lambda \
    "${PROJECT_NAME}-notification-handler" \
    "/tmp/notification-handler.zip" \
    "lambda_function.lambda_handler" \
    "python3.11" \
    "512" \
    "60" \
    "arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-notification-lambda-role"

# Deploy Tracking Updater Lambda
echo -e "\n${YELLOW}=== Deploying Tracking Updater ===${NC}"
package_lambda \
    "tracking-updater" \
    "services/tracking_updater" \
    "/tmp/tracking-updater.zip"

deploy_lambda \
    "${PROJECT_NAME}-tracking-updater" \
    "/tmp/tracking-updater.zip" \
    "lambda_function.lambda_handler" \
    "python3.11" \
    "1024" \
    "180" \
    "arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-tracking-lambda-role"

# Cleanup
echo -e "\n${YELLOW}Cleaning up temporary files...${NC}"
rm -f /tmp/eligibility-engine.zip
rm -f /tmp/document-processor.zip
rm -f /tmp/ocr-processor.zip
rm -f /tmp/notification-handler.zip
rm -f /tmp/tracking-updater.zip

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
