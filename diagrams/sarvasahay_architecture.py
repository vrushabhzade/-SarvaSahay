from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Lambda
from diagrams.aws.database import RDS, Dynamodb, ElasticacheForRedis
from diagrams.aws.network import APIGateway, ELB, CloudFront
from diagrams.aws.storage import S3
from diagrams.aws.ml import Sagemaker
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.security import IAM
from diagrams.onprem.client import Users
from diagrams.onprem.network import Internet

with Diagram("SarvaSahay Platform - AWS Architecture", show=False, direction="TB"):
    
    # Users and Interfaces
    with Cluster("User Interfaces"):
        users = Users("Rural Citizens")
        sms = Lambda("SMS Interface")
        voice = Lambda("Voice Interface")
        web = CloudFront("Web App")
        mobile = CloudFront("Mobile App")
    
    # API Gateway
    api_gateway = APIGateway("API Gateway")
    load_balancer = ELB("Load Balancer")
    
    # Core Microservices
    with Cluster("Core Services"):
        profile_service = ECS("Profile Service")
        eligibility_engine = ECS("Eligibility Engine")
        document_processor = ECS("Document Processor")
        auto_application = ECS("Auto-Application Service")
        tracking_service = ECS("Tracking Service")
        notification_service = ECS("Notification Service")
    
    # AI/ML Components
    with Cluster("AI/ML Layer"):
        xgboost_model = Sagemaker("XGBoost Model")
        ocr_engine = Lambda("OCR Engine")
        nlp_processor = Lambda("NLP Processor")
    
    # Data Layer
    with Cluster("Data Layer"):
        user_db = RDS("User Database")
        scheme_db = RDS("Scheme Database")
        document_store = S3("Document Store")
        cache = ElasticacheForRedis("Redis Cache")
    
    # External Systems
    with Cluster("Government APIs"):
        pm_kisan = Internet("PM-KISAN API")
        dbt_system = Internet("DBT System")
        pfms = Internet("PFMS")
        state_apis = Internet("State APIs")
    
    # Message Queue
    event_queue = SQS("Event Queue")
    notifications = SNS("Notifications")
    
    # Security
    security = IAM("IAM & Security")
    
    # User flows
    users >> [sms, voice, web, mobile]
    [sms, voice, web, mobile] >> api_gateway
    api_gateway >> load_balancer
    
    # Service connections
    load_balancer >> [profile_service, eligibility_engine, document_processor, 
                     auto_application, tracking_service, notification_service]
    
    # AI/ML connections
    eligibility_engine >> xgboost_model
    document_processor >> ocr_engine
    voice >> nlp_processor
    
    # Data connections
    profile_service >> user_db
    eligibility_engine >> scheme_db
    document_processor >> document_store
    [profile_service, eligibility_engine] >> cache
    
    # External API connections
    auto_application >> [pm_kisan, dbt_system, state_apis]
    tracking_service >> pfms
    
    # Event-driven communication
    [profile_service, eligibility_engine, auto_application, tracking_service] >> event_queue
    event_queue >> notification_service
    notification_service >> notifications
    
    # Security layer
    security >> [api_gateway, load_balancer]