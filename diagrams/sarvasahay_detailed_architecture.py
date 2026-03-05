from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Lambda, Fargate
from diagrams.aws.database import RDS, Dynamodb, ElasticacheForRedis
from diagrams.aws.network import APIGateway, ELB, CloudFront, VPC
from diagrams.aws.storage import S3
from diagrams.aws.ml import Sagemaker, Textract
from diagrams.aws.integration import SQS, SNS, Eventbridge
from diagrams.aws.security import IAM, SecretsManager, KMS
from diagrams.aws.analytics import Kinesis, Glue
from diagrams.aws.management import Cloudwatch
from diagrams.aws.devtools import XRay
from diagrams.onprem.client import Users
from diagrams.onprem.network import Internet
from diagrams.generic.device import Mobile, Tablet

# Main Architecture Diagram
with Diagram("SarvaSahay Platform - Detailed AWS Architecture", show=False, direction="TB", filename="sarvasahay_detailed"):
    
    # User Interfaces Layer
    with Cluster("Multi-Channel User Interfaces"):
        rural_users = Users("Rural Citizens")
        sms_users = Mobile("SMS Users")
        voice_users = Tablet("Voice Users")
        web_users = Users("Web Users")
        mobile_users = Mobile("Mobile App Users")
    
    # Edge and CDN
    cdn = CloudFront("CloudFront CDN")
    
    # API Gateway and Load Balancing
    with Cluster("API Gateway Layer"):
        api_gateway = APIGateway("API Gateway v2")
        load_balancer = ELB("Application Load Balancer")
        
    # VPC and Security
    with Cluster("VPC - Secure Network"):
        # Core Microservices (Containerized)
        with Cluster("Core Services (ECS Fargate)"):
            profile_service = Fargate("Profile Service")
            eligibility_engine = Fargate("Eligibility Engine")
            document_processor = Fargate("Document Processor")
            auto_application = Fargate("Auto-Application Service")
            tracking_service = Fargate("Tracking Service")
            notification_service = Fargate("Notification Service")
        
        # Serverless Functions
        with Cluster("Serverless Functions"):
            sms_handler = Lambda("SMS Handler")
            voice_handler = Lambda("Voice Handler")
            ocr_processor = Lambda("OCR Processor")
            nlp_processor = Lambda("NLP Processor")
            webhook_handler = Lambda("Webhook Handler")
        
        # AI/ML Services
        with Cluster("AI/ML Services"):
            xgboost_endpoint = Sagemaker("XGBoost Endpoint")
            textract_ocr = Textract("Textract OCR")
            sagemaker_training = Sagemaker("Model Training")
        
        # Data Layer
        with Cluster("Data Layer"):
            # Primary Databases
            user_db = RDS("User Database\n(PostgreSQL)")
            scheme_db = RDS("Scheme Database\n(PostgreSQL)")
            
            # NoSQL for Documents
            document_metadata = Dynamodb("Document Metadata\n(DynamoDB)")
            
            # Object Storage
            document_store = S3("Document Store\n(S3)")
            model_artifacts = S3("ML Model Artifacts\n(S3)")
            
            # Caching
            redis_cache = ElasticacheForRedis("Redis Cache\n(Profile & Scheme Data)")
        
        # Event-Driven Architecture
        with Cluster("Event & Messaging"):
            event_bus = Eventbridge("EventBridge")
            sqs_queue = SQS("SQS Queues")
            sns_notifications = SNS("SNS Topics")
            kinesis_stream = Kinesis("Kinesis Data Stream")
        
        # Security Services
        with Cluster("Security & Secrets"):
            iam_roles = IAM("IAM Roles & Policies")
            secrets_manager = SecretsManager("Secrets Manager")
            kms_encryption = KMS("KMS Encryption")
        
        # Monitoring & Observability
        with Cluster("Monitoring"):
            cloudwatch = Cloudwatch("CloudWatch")
            xray_tracing = XRay("X-Ray Tracing")
            glue_etl = Glue("Glue ETL")
    
    # External Government Systems
    with Cluster("Government Integration"):
        pm_kisan_api = Internet("PM-KISAN API")
        dbt_system = Internet("DBT System")
        pfms_api = Internet("PFMS API")
        state_govt_apis = Internet("State Government APIs")
    
    # User Interface Connections
    [rural_users, sms_users, voice_users] >> sms_handler
    [rural_users, voice_users] >> voice_handler
    [web_users, mobile_users] >> cdn >> api_gateway
    
    # API Gateway routing
    api_gateway >> load_balancer
    load_balancer >> [profile_service, eligibility_engine, document_processor, 
                     auto_application, tracking_service, notification_service]
    
    # SMS and Voice processing
    sms_handler >> [profile_service, notification_service]
    voice_handler >> nlp_processor >> profile_service
    
    # Document processing flow
    document_processor >> [ocr_processor, textract_ocr]
    ocr_processor >> document_store
    textract_ocr >> document_metadata
    
    # AI/ML connections
    eligibility_engine >> xgboost_endpoint
    xgboost_endpoint >> model_artifacts
    sagemaker_training >> model_artifacts
    
    # Data layer connections
    profile_service >> [user_db, redis_cache]
    eligibility_engine >> [scheme_db, redis_cache]
    document_processor >> [document_store, document_metadata]
    
    # Event-driven communication
    [profile_service, eligibility_engine, auto_application, tracking_service] >> event_bus
    event_bus >> sqs_queue >> notification_service
    notification_service >> sns_notifications
    
    # Analytics and monitoring
    [profile_service, eligibility_engine, document_processor, auto_application, 
     tracking_service, notification_service] >> kinesis_stream
    kinesis_stream >> glue_etl
    
    # Government API integration
    auto_application >> [pm_kisan_api, dbt_system, state_govt_apis]
    tracking_service >> pfms_api
    webhook_handler >> tracking_service
    
    # Security integration
    iam_roles >> [profile_service, eligibility_engine, document_processor, 
                  auto_application, tracking_service, notification_service]
    secrets_manager >> [auto_application, tracking_service]
    kms_encryption >> [user_db, scheme_db, document_store]
    
    # Monitoring connections
    [profile_service, eligibility_engine, document_processor, auto_application, 
     tracking_service, notification_service] >> cloudwatch
    [api_gateway, load_balancer] >> xray_tracing

# Data Flow Diagram
with Diagram("SarvaSahay - Data Flow Architecture", show=False, direction="LR", filename="sarvasahay_dataflow"):
    
    # Input Sources
    with Cluster("Data Sources"):
        user_input = Users("User Profile Data")
        document_upload = Mobile("Document Upload")
        govt_schemes = Internet("Government Scheme Data")
        outcome_data = Internet("Application Outcomes")
    
    # Processing Layer
    with Cluster("Data Processing"):
        profile_validation = Lambda("Profile Validation")
        ocr_extraction = Textract("OCR Text Extraction")
        scheme_ingestion = Lambda("Scheme Data Ingestion")
        outcome_tracking = Lambda("Outcome Tracking")
    
    # ML Pipeline
    with Cluster("ML Pipeline"):
        feature_engineering = Glue("Feature Engineering")
        model_training = Sagemaker("XGBoost Training")
        model_inference = Sagemaker("Eligibility Inference")
    
    # Storage Layer
    with Cluster("Data Storage"):
        raw_data = S3("Raw Data Lake")
        processed_data = S3("Processed Data")
        user_profiles = RDS("User Profiles DB")
        scheme_rules = RDS("Scheme Rules DB")
        ml_models = S3("ML Model Store")
    
    # Analytics Layer
    with Cluster("Analytics & Insights"):
        analytics_engine = Glue("Analytics Engine")
        performance_metrics = Cloudwatch("Performance Metrics")
        business_intelligence = Lambda("BI Reports")
    
    # Data flow connections
    user_input >> profile_validation >> user_profiles
    document_upload >> ocr_extraction >> processed_data
    govt_schemes >> scheme_ingestion >> scheme_rules
    outcome_data >> outcome_tracking >> raw_data
    
    # ML pipeline flow
    [user_profiles, scheme_rules, processed_data] >> feature_engineering
    feature_engineering >> model_training >> ml_models
    ml_models >> model_inference
    
    # Analytics flow
    [user_profiles, scheme_rules, processed_data, raw_data] >> analytics_engine
    analytics_engine >> performance_metrics
    performance_metrics >> business_intelligence

# Security Architecture
with Diagram("SarvaSahay - Security Architecture", show=False, direction="TB", filename="sarvasahay_security"):
    
    # External Access
    internet = Internet("Internet")
    
    # WAF and DDoS Protection
    with Cluster("Edge Security"):
        waf = CloudFront("WAF + CloudFront")
        ddos_protection = CloudFront("DDoS Protection")
    
    # API Security
    with Cluster("API Security Layer"):
        api_gateway_auth = APIGateway("API Gateway\n(OAuth 2.0 + JWT)")
        rate_limiting = APIGateway("Rate Limiting")
    
    # Network Security
    with Cluster("Network Security (VPC)"):
        public_subnet = VPC("Public Subnet")
        private_subnet = VPC("Private Subnet")
        isolated_subnet = VPC("Isolated Subnet")
    
    # Application Security
    with Cluster("Application Security"):
        iam_service_roles = IAM("Service Roles")
        secrets_mgmt = SecretsManager("API Keys & Secrets")
        encryption_service = KMS("Encryption at Rest")
    
    # Data Security
    with Cluster("Data Protection"):
        encrypted_db = RDS("Encrypted Databases")
        encrypted_storage = S3("Encrypted S3 Buckets")
        secure_cache = ElasticacheForRedis("Encrypted Redis")
    
    # Monitoring & Compliance
    with Cluster("Security Monitoring"):
        security_logs = Cloudwatch("Security Logs")
        audit_trail = Cloudwatch("Audit Trail")
        compliance_reports = Lambda("Compliance Reports")
    
    # Security flow
    internet >> waf >> api_gateway_auth
    api_gateway_auth >> public_subnet
    public_subnet >> private_subnet >> isolated_subnet
    
    # Security services
    iam_service_roles >> [public_subnet, private_subnet, isolated_subnet]
    secrets_mgmt >> private_subnet
    encryption_service >> [encrypted_db, encrypted_storage, secure_cache]
    
    # Monitoring
    [public_subnet, private_subnet, isolated_subnet] >> security_logs
    security_logs >> audit_trail >> compliance_reports

print("AWS Architecture diagrams created successfully!")
print("Generated files:")
print("- sarvasahay_detailed.png - Comprehensive architecture")
print("- sarvasahay_dataflow.png - Data flow and ML pipeline")
print("- sarvasahay_security.png - Security architecture")