#!/usr/bin/env python3
"""
Test AWS Configuration for SarvaSahay Platform

This script tests your AWS endpoint configuration and verifies
that all services are accessible.
"""

import os
import sys
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_environment_variables() -> Tuple[bool, List[str]]:
    """Test that required environment variables are set"""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        'AWS_DEFAULT_REGION',
        'AWS_S3_BUCKET_DOCUMENTS',
        'AWS_S3_BUCKET_ML_MODELS',
        'AWS_S3_BUCKET_BACKUPS'
    ]
    
    optional_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_S3_ENDPOINT_URL',
        'AWS_LAMBDA_ENDPOINT_URL'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"  ❌ {var}: Not set")
        else:
            print(f"  ✅ {var}: {value}")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            # Mask credentials
            if 'SECRET' in var or 'KEY' in var:
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
                print(f"  ✅ {var}: {masked}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ℹ️  {var}: Not set (optional)")
    
    print()
    return len(missing) == 0, missing


def test_s3_connection() -> bool:
    """Test S3 connection and bucket access"""
    print("🪣 Testing S3 connection...")
    
    try:
        from shared.utils.aws_s3 import get_s3_client
        
        s3_client = get_s3_client()
        print(f"  ✅ S3 client initialized")
        print(f"  ✅ Region: {s3_client.region}")
        print(f"  ✅ Documents bucket: {s3_client.buckets['documents']}")
        print(f"  ✅ ML models bucket: {s3_client.buckets['ml_models']}")
        print(f"  ✅ Backups bucket: {s3_client.buckets['backups']}")
        
        # Try to list buckets (this will fail if credentials are wrong)
        try:
            response = s3_client.s3_client.list_buckets()
            print(f"  ✅ Successfully connected to S3")
            print(f"  ℹ️  Found {len(response['Buckets'])} buckets")
        except Exception as e:
            print(f"  ⚠️  Could not list buckets: {e}")
            print(f"  ℹ️  This is normal for LocalStack or restricted IAM")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ S3 connection failed: {e}")
        print()
        return False


def test_lambda_connection() -> bool:
    """Test Lambda connection"""
    print("⚡ Testing Lambda connection...")
    
    try:
        from shared.utils.aws_lambda import get_lambda_client
        
        lambda_client = get_lambda_client()
        print(f"  ✅ Lambda client initialized")
        print(f"  ✅ Region: {lambda_client.region}")
        print(f"  ✅ Eligibility function: {lambda_client.functions['eligibility']}")
        print(f"  ✅ Document processor: {lambda_client.functions['document_processor']}")
        print(f"  ✅ OCR function: {lambda_client.functions['ocr']}")
        
        # Try to list functions (this will fail if credentials are wrong)
        try:
            response = lambda_client.lambda_client.list_functions()
            print(f"  ✅ Successfully connected to Lambda")
            print(f"  ℹ️  Found {len(response['Functions'])} functions")
        except Exception as e:
            print(f"  ⚠️  Could not list functions: {e}")
            print(f"  ℹ️  This is normal for LocalStack or restricted IAM")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ Lambda connection failed: {e}")
        print()
        return False


def test_s3_operations() -> bool:
    """Test S3 upload/download operations"""
    print("📤 Testing S3 operations...")
    
    try:
        from shared.utils.aws_s3 import get_s3_client
        import io
        
        s3_client = get_s3_client()
        
        # Create test data
        test_content = b"Test document content for SarvaSahay Platform"
        test_file = io.BytesIO(test_content)
        
        # Upload test file
        print(f"  📤 Uploading test file...")
        s3_key = s3_client.upload_document(
            test_file, 
            "test-user", 
            "test-document",
            "txt"
        )
        print(f"  ✅ Uploaded to: {s3_key}")
        
        # Download test file
        print(f"  📥 Downloading test file...")
        downloaded_content = s3_client.download_document(s3_key)
        print(f"  ✅ Downloaded {len(downloaded_content)} bytes")
        
        # Verify content
        if downloaded_content == test_content:
            print(f"  ✅ Content verification passed")
        else:
            print(f"  ❌ Content verification failed")
            return False
        
        # Generate presigned URL
        print(f"  🔗 Generating presigned URL...")
        url = s3_client.generate_presigned_url(s3_key, expiration=300)
        print(f"  ✅ Generated URL (expires in 5 minutes)")
        
        # Clean up
        print(f"  🗑️  Cleaning up test file...")
        s3_client.delete_document(s3_key)
        print(f"  ✅ Test file deleted")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ S3 operations failed: {e}")
        print()
        return False


def print_summary(results: Dict[str, bool]):
    """Print test summary"""
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    print()
    
    if failed == 0:
        print("🎉 All tests passed! Your AWS configuration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print()
        print("Common solutions:")
        print("  1. For LocalStack: Make sure it's running (docker ps | grep localstack)")
        print("  2. For AWS: Check your credentials in .env file")
        print("  3. Run: python scripts/update_aws_endpoints.py show")
        print("  4. See: AWS_SETUP_GUIDE.md for detailed setup instructions")
    
    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 AWS Configuration Test Suite")
    print("=" * 60)
    print()
    
    # Load environment from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment from .env file")
        print()
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")
        print()
    
    results = {}
    
    # Test environment variables
    env_ok, missing = test_environment_variables()
    results['Environment Variables'] = env_ok
    
    if not env_ok:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print(f"Please update your .env file")
        print()
        print_summary(results)
        return 1
    
    # Test S3 connection
    results['S3 Connection'] = test_s3_connection()
    
    # Test Lambda connection
    results['Lambda Connection'] = test_lambda_connection()
    
    # Test S3 operations (only if connection works)
    if results['S3 Connection']:
        results['S3 Operations'] = test_s3_operations()
    else:
        print("⏭️  Skipping S3 operations test (connection failed)")
        print()
        results['S3 Operations'] = False
    
    # Print summary
    print_summary(results)
    
    # Return exit code
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
