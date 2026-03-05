from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Lambda, Fargate, EC2
from diagrams.aws.database import RDS, ElasticacheForRedis
from diagrams.aws.network import APIGateway, ELB, VPC, PrivateSubnet, PublicSubnet
from diagrams.aws.storage import S3
from diagrams.aws.ml import Sagemaker
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.devtools import Codebuild, Codedeploy, Codepipeline
from diagrams.aws.management import Cloudformation, Cloudwatch
from diagrams.aws.security import IAM
from diagrams.onprem.ci import Jenkins
from diagrams.onprem.vcs import Git

# Deployment Architecture
with Diagram("SarvaSahay - Deployment Architecture", show=False, direction="TB", filename="sarvasahay_deployment"):
    
    # Development & CI/CD
    with Cluster("Development & CI/CD"):
        git_repo = Git("Git Repository")
        ci_pipeline = Codepipeline("CodePipeline")
        build_service = Codebuild("CodeBuild")
        deploy_service = Codedeploy("CodeDeploy")
        iac_templates = Cloudformation("CloudFormation\nTemplates")
    
    # Multi-Environment Setup
    with Cluster("Development Environment"):
        dev_vpc = VPC("Dev VPC")
        with Cluster("Dev Services"):
            dev_api = APIGateway("Dev API Gateway")
            dev_services = ECS("Dev Services")
            dev_db = RDS("Dev Database")
    
    with Cluster("Staging Environment"):
        staging_vpc = VPC("Staging VPC")
        with Cluster("Staging Services"):
            staging_api = APIGateway("Staging API Gateway")
            staging_services = ECS("Staging Services")
            staging_db = RDS("Staging Database")
    
    with Cluster("Production Environment"):
        prod_vpc = VPC("Production VPC")
        
        # Production Public Subnet
        with Cluster("Public Subnet (DMZ)"):
            prod_alb = ELB("Production ALB")
            prod_api = APIGateway("Production API Gateway")
            nat_gateway = EC2("NAT Gateway")
        
        # Production Private Subnet
        with Cluster("Private Subnet (Application Layer)"):
            # Microservices in ECS Fargate
            profile_svc = Fargate("Profile Service\n(Multi-AZ)")
            eligibility_svc = Fargate("Eligibility Engine\n(Multi-AZ)")
            document_svc = Fargate("Document Processor\n(Multi-AZ)")
            application_svc = Fargate("Auto-Application\n(Multi-AZ)")
            tracking_svc = Fargate("Tracking Service\n(Multi-AZ)")
            notification_svc = Fargate("Notification Service\n(Multi-AZ)")
            
            # Serverless Functions
            lambda_functions = Lambda("Lambda Functions\n(SMS, Voice, OCR)")
        
        # Production Database Subnet (Isolated)
        with Cluster("Database Subnet (Isolated)"):
            prod_db_primary = RDS("Primary Database\n(Multi-AZ)")
            prod_db_replica = RDS("Read Replica\n(Cross-Region)")
            prod_cache = ElasticacheForRedis("Redis Cluster\n(Multi-AZ)")
        
        # ML Infrastructure
        with Cluster("ML Infrastructure"):
            ml_endpoint = Sagemaker("SageMaker Endpoint\n(Auto-scaling)")
            ml_training = Sagemaker("Training Jobs\n(Spot Instances)")
            model_store = S3("Model Artifacts\n(Versioned)")
        
        # Shared Services
        with Cluster("Shared Services"):
            document_storage = S3("Document Storage\n(Cross-Region Replication)")
            event_queue = SQS("Event Queues\n(DLQ Enabled)")
            notifications = SNS("Notification Topics")
            monitoring = Cloudwatch("CloudWatch\n(Alarms & Dashboards)")
    
    # Disaster Recovery
    with Cluster("Disaster Recovery (Secondary Region)"):
        dr_vpc = VPC("DR VPC")
        dr_db = RDS("DR Database\n(Cross-Region Backup)")
        dr_storage = S3("DR Storage\n(Cross-Region Sync)")
    
    # CI/CD Flow
    git_repo >> ci_pipeline
    ci_pipeline >> build_service >> deploy_service
    deploy_service >> iac_templates
    
    # Deployment Flow
    iac_templates >> [dev_vpc, staging_vpc, prod_vpc]
    
    # Development Environment
    dev_api >> dev_services >> dev_db
    
    # Staging Environment  
    staging_api >> staging_services >> staging_db
    
    # Production Environment Flow
    prod_api >> prod_alb
    prod_alb >> [profile_svc, eligibility_svc, document_svc, 
                application_svc, tracking_svc, notification_svc]
    
    # Database connections
    [profile_svc, eligibility_svc] >> prod_db_primary
    [document_svc, application_svc, tracking_svc] >> prod_db_replica
    [profile_svc, eligibility_svc] >> prod_cache
    
    # ML connections
    eligibility_svc >> ml_endpoint
    ml_training >> model_store >> ml_endpoint
    
    # Storage and messaging
    document_svc >> document_storage
    [profile_svc, eligibility_svc, application_svc, tracking_svc] >> event_queue
    event_queue >> notification_svc >> notifications
    
    # Monitoring
    [profile_svc, eligibility_svc, document_svc, application_svc, 
     tracking_svc, notification_svc] >> monitoring
    
    # Disaster Recovery
    prod_db_primary >> dr_db
    document_storage >> dr_storage

# Infrastructure as Code Structure
with Diagram("SarvaSahay - Infrastructure as Code", show=False, direction="LR", filename="sarvasahay_iac"):
    
    # Source Control
    with Cluster("Source Control"):
        terraform_modules = Git("Terraform Modules")
        cloudformation_templates = Git("CloudFormation Templates")
        helm_charts = Git("Helm Charts")
        config_files = Git("Configuration Files")
    
    # CI/CD Pipeline
    with Cluster("CI/CD Pipeline"):
        pipeline_trigger = Codepipeline("Pipeline Trigger")
        validation_stage = Codebuild("Validation & Testing")
        deployment_stage = Codedeploy("Deployment Stage")
    
    # Infrastructure Provisioning
    with Cluster("Infrastructure Provisioning"):
        network_stack = Cloudformation("Network Stack\n(VPC, Subnets, Security Groups)")
        compute_stack = Cloudformation("Compute Stack\n(ECS, Lambda, SageMaker)")
        data_stack = Cloudformation("Data Stack\n(RDS, S3, ElastiCache)")
        security_stack = Cloudformation("Security Stack\n(IAM, KMS, Secrets)")
    
    # Environment Management
    with Cluster("Environment Management"):
        dev_env = Cloudformation("Development")
        staging_env = Cloudformation("Staging")
        prod_env = Cloudformation("Production")
        dr_env = Cloudformation("Disaster Recovery")
    
    # Configuration Management
    with Cluster("Configuration Management"):
        parameter_store = Cloudformation("Parameter Store")
        secrets_manager = Cloudformation("Secrets Manager")
        config_service = Cloudformation("Config Service")
    
    # IaC Flow
    [terraform_modules, cloudformation_templates, helm_charts, config_files] >> pipeline_trigger
    pipeline_trigger >> validation_stage >> deployment_stage
    
    # Stack deployment
    deployment_stage >> [network_stack, compute_stack, data_stack, security_stack]
    
    # Environment provisioning
    network_stack >> [dev_env, staging_env, prod_env, dr_env]
    compute_stack >> [dev_env, staging_env, prod_env, dr_env]
    data_stack >> [dev_env, staging_env, prod_env, dr_env]
    security_stack >> [dev_env, staging_env, prod_env, dr_env]
    
    # Configuration management
    parameter_store >> [dev_env, staging_env, prod_env, dr_env]
    secrets_manager >> [dev_env, staging_env, prod_env, dr_env]
    config_service >> [dev_env, staging_env, prod_env, dr_env]

print("Deployment architecture diagrams created successfully!")
print("Generated files:")
print("- sarvasahay_deployment.png - Multi-environment deployment architecture")
print("- sarvasahay_iac.png - Infrastructure as Code structure")