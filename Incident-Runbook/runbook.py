#!/usr/bin/env python3
"""
AI Incident Runbook Generator
Generates step-by-step runbooks from incident alerts using Claude.
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


RUNBOOK_PROMPT = """You are a senior Site Reliability Engineer (SRE) responding to a production incident.

Given the alert below, generate a clear, actionable runbook with these sections:

## Incident Summary
One sentence describing what is likely happening and the impact.

## Severity
Rate as P1 (critical, full outage) / P2 (major, partial outage) / P3 (minor, degraded) and why.

## Immediate Actions (first 5 minutes)
Quick steps to assess and stabilize. Include the exact shell commands to run.

## Diagnostic Steps
Step-by-step investigation to find the root cause. Include exact commands with expected output examples.

## Fix Options
List possible fixes from most likely to least likely. For each, include the command to apply it.

## Escalation
When and who to escalate to if not resolved within 15 minutes.

## Prevention
One or two things to do after the incident to prevent recurrence.

Use exact, copy-pasteable shell commands. Be concise and direct — this is for an engineer under pressure at 2am.

---
ALERT:
{alert}
---"""


def generate_runbook(alert: str, keyvault_url: str = None) -> str:
    api_key = get_api_key(keyvault_url)
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": RUNBOOK_PROMPT.format(alert=alert)}
        ],
    )
    return message.content[0].text


def save_runbook(content: str, alert: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = alert[:30].lower().replace(" ", "_").replace("/", "_")
    out_path = f"runbook_{slug}_{timestamp}.md"
    Path(out_path).write_text(content, encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="AI Incident Runbook Generator using Claude"
    )
    parser.add_argument("alert", help="Alert description (e.g. 'CPU 95pct on prod-web-01')")
    parser.add_argument("--save", action="store_true", help="Save runbook as markdown file")
    parser.add_argument("--keyvault", help="Azure Key Vault URL (e.g. https://my-vault.vault.azure.net)", default=None)
    args = parser.parse_args()

    print(f"Generating runbook for: {args.alert}\n")
    runbook = generate_runbook(args.alert, keyvault_url=args.keyvault)

    print("=" * 60)
    print("  AI INCIDENT RUNBOOK")
    print("=" * 60)
    print(runbook)
    print("=" * 60)

    if args.save:
        out = save_runbook(runbook, args.alert)
        print(f"\nRunbook saved to: {out}")


if __name__ == "__main__":
    main()
