# AI Terraform Plan Reviewer

An AI-powered CLI tool that analyzes `terraform plan` output using Claude and returns a structured security, cost, and best-practice review — before you apply anything.

## Why

Manually reviewing Terraform plans is slow and error-prone. This tool sends the plan to Claude and gets back a structured report flagging security risks, cost surprises, and violations — in seconds.

## What it checks

- **Security** — open ports, public access, missing encryption, overly permissive IAM, exposed secrets
- **Cost** — expensive instance types, large storage allocations, unexpected resources
- **Best practices** — missing tags, hardcoded values, disabled versioning, skipped snapshots
- **Risk level** — LOW / MEDIUM / HIGH summary

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
# Review a plan file
python reviewer.py sample_plan.txt

# Review and save the report as markdown
python reviewer.py sample_plan.txt --save
```

### Getting a plan file from Terraform

```bash
terraform plan -out=tfplan
terraform show -no-color tfplan > plan.txt
python reviewer.py plan.txt
```

## Example output

```
================================================================
  AI TERRAFORM PLAN REVIEW
================================================================
## 1. Change Summary
- Creating: S3 bucket, security group, EC2 instance, RDS instance
- Modifying: IAM role (lambda_exec)
- Destroying: nothing

## 2. Security Concerns
- [CRITICAL] S3 bucket has public-read ACL — exposes all data publicly
- [CRITICAL] Security group allows ALL TCP ports (0-65535) from 0.0.0.0/0
- [CRITICAL] RDS instance is publicly accessible and storage is NOT encrypted
- [CRITICAL] IAM role policy uses Action: *, Principal: * — grants full AWS access to anyone
- [CRITICAL] EC2 user_data contains hardcoded credentials: SENSITIVE_DB_PASSWORD

## 3. Cost Implications
- db.r5.4xlarge RDS instance — ~$700-900/month
- 500 GB allocated storage — additional cost
- t3.2xlarge EC2 — ~$240/month

## 4. Best Practice Violations
- S3 versioning is Disabled
- RDS skip_final_snapshot = true — no backup on deletion
- No resource tags on any resource

## 5. Overall Risk Level
HIGH — multiple critical security vulnerabilities including public data exposure, 
open firewall rules, unencrypted database, and overprivileged IAM role.
================================================================
```

## Built with

- [Claude](https://anthropic.com) (claude-sonnet-4-6) — AI analysis
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
