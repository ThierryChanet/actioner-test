#!/usr/bin/env python3
import os
from anthropic import Anthropic

# Get API key from env
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    # Try loading from .env
    try:
        with open(".env") as f:
            for line in f:
                if line.startswith("ANTHROPIC_API_KEY"):
                    api_key = line.split("=")[1].strip().strip('"')
                    break
    except:
        pass

print(f"API Key: {api_key[:20]}..." if api_key else "No key found")

client = Anthropic(api_key=api_key)

# Test basic API
print("\nTesting claude-3-sonnet-20240229...")
try:
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say hello in 5 words"}]
    )
    print(f"✓ Working! Response: {response.content[0].text}")
except Exception as e:
    print(f"✗ Error: {e}")
