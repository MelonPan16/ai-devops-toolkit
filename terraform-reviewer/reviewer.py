#!/usr/bin/env python3
"""
AI Terraform Plan Reviewer
Sends terraform plan output to Claude for security, cost, and best-practice analysis.
"""

import anthropic
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")


def get_api_key(keyvault_url: str = None) -> str:
    """
    Gets the Anthropic API key.
    - If --keyvault is passed: reads from Azure Key Vault using DefaultAzureCredential
      (works with Managed Identity on Azure, or 'az login' on a laptop)
    - Otherwise: reads from ANTHROPIC_API_KEY environment variable
    """
    if keyvault_url:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=keyvault_url, credential=credential)
        return client.get_secret("ANTHROPIC-API-KEY").value

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Use --keyvault or set the env var.")
        sys.exit(1)
    return api_key


REVIEW_PROMPT = """You are a senior DevOps/Cloud security engineer reviewing a Terraform plan.
Analyze the plan below and return a structured review with these sections:

## 1. Change Summary
Brief list of what will be created, modified, and destroyed.

## 2. Security Concerns
Flag any resources with open ports, public access, missing encryption, overly permissive IAM, exposed secrets, etc.

## 3. Cost Implications
Flag expensive resources, unexpected scaling, or anything that could spike the bill.

## 4. Best Practice Violations
Missing tags, hardcoded values, missing lifecycle rules, naming issues, etc.

## 5. Overall Risk Level
Rate as LOW / MEDIUM / HIGH and give a one-line justification.

Be concise and actionable. Use bullet points. Mark critical issues with [CRITICAL].

---
TERRAFORM PLAN:
{plan}
---"""


def load_plan(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"Error: '{path}' not found.")
        sys.exit(1)
    return p.read_text(encoding="utf-8")


def review(plan_text: str, keyvault_url: str = None) -> str:
    api_key = get_api_key(keyvault_url)
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": REVIEW_PROMPT.format(plan=plan_text)}
        ],
    )
    return message.content[0].text


def save_report(report: str, plan_path: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(plan_path).stem + f"_review_{timestamp}.md"
    Path(out_path).write_text(report, encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered Terraform Plan Reviewer using Claude"
    )
    parser.add_argument("plan_file", help="Path to terraform plan output (.txt)")
    parser.add_argument("--save", action="store_true", help="Save report as a markdown file")
    parser.add_argument("--keyvault", help="Azure Key Vault URL (e.g. https://my-vault.vault.azure.net)", default=None)
    args = parser.parse_args()

    plan_text = load_plan(args.plan_file)

    print("Analyzing Terraform plan with Claude AI...\n")
    report = review(plan_text, keyvault_url=args.keyvault)

    print("=" * 60)
    print("  AI TERRAFORM PLAN REVIEW")
    print("=" * 60)
    print(report)
    print("=" * 60)

    if args.save:
        out = save_report(report, args.plan_file)
        print(f"\nReport saved to: {out}")


if __name__ == "__main__":
    main()
