# Infrastructure as Code (Terraform)

This directory contains the Terraform configuration files used to provision our AWS infrastructure in a reproducible way.

## Directory Structure
- `networking/`: VPC, Subnets, Internet Gateways, NAT Gateways, Security Groups.
- `database/`: Amazon Aurora PostgreSQL / RDS instances.
- `compute/`: ECS/EKS resources.
- `security/`: KMS keys, AWS Secrets Manager, Cognito, Cross-account IAM roles.
