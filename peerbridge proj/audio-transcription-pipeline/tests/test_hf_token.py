#!/usr/bin/env python3
"""
Test HuggingFace Token Setup
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("HuggingFace Token Verification")
print("="*60)
print()

# Check if token exists
hf_token = os.getenv("HF_TOKEN")

if not hf_token:
    print("❌ HF_TOKEN not found in .env file")
    print()
    print("Steps to fix:")
    print("1. Go to https://huggingface.co/settings/tokens")
    print("2. Click 'New token'")
    print("3. Copy the token (starts with 'hf_')")
    print("4. Add to .env file: HF_TOKEN=hf_your_token_here")
    exit(1)

if not hf_token.startswith("hf_"):
    print("⚠️  Token found but doesn't start with 'hf_'")
    print(f"   Current value: {hf_token[:10]}...")
    print("   Make sure you copied the full token from HuggingFace")
    exit(1)

print(f"✅ Token found: {hf_token[:10]}...{hf_token[-4:]}")
print()

# Try to access the model
print("Testing model access...")
try:
    from huggingface_hub import hf_hub_download

    # Try to download model info (doesn't actually download the model)
    print("Checking if you have access to pyannote/speaker-diarization-3.1...")

    file = hf_hub_download(
        repo_id="pyannote/speaker-diarization-3.1",
        filename="config.yaml",
        token=hf_token
    )

    print("✅ Model access confirmed!")
    print()
    print("="*60)
    print("SUCCESS! Your HuggingFace setup is complete.")
    print("="*60)

except Exception as e:
    error_msg = str(e)

    if "gated" in error_msg.lower() or "access" in error_msg.lower():
        print("❌ Model access denied")
        print()
        print("You need to accept the model terms:")
        print("1. Go to https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("2. Click 'Agree and access repository'")
        print("3. Fill out the form and submit")
        print("4. Run this script again")
    elif "401" in error_msg or "unauthorized" in error_msg.lower():
        print("❌ Invalid token")
        print()
        print("Your token might be wrong. Generate a new one:")
        print("1. Go to https://huggingface.co/settings/tokens")
        print("2. Click 'New token'")
        print("3. Copy the full token")
        print("4. Update .env file")
    else:
        print(f"❌ Error: {error_msg}")
        print()
        print("This might be a network issue or HuggingFace is down.")
        print("Try again in a few minutes.")
