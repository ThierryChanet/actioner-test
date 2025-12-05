#!/usr/bin/env python3
import os
from anthropic import Anthropic

# Get API key
api_key = None
try:
    with open(".env") as f:
        for line in f:
            if line.startswith("ANTHROPIC_API_KEY"):
                api_key = line.split("=")[1].strip().strip('"')
                break
except:
    pass

print(f"API Key loaded: {bool(api_key)}")
if api_key:
    print(f"Key prefix: {api_key[:20]}...")

client = Anthropic(api_key=api_key)

# Try different models
models_to_test = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
    "claude-3-sonnet-20240229",
]

for model in models_to_test:
    print(f"\nTrying {model}...")
    try:
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"  ✓ SUCCESS! Model works!")
        print(f"  Response: {response.content[0].text}")
        break
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            print(f"  ✗ 404 - Model not found")
        elif "401" in error_str:
            print(f"  ✗ 401 - Authentication failed")
        elif "403" in error_str:
            print(f"  ✗ 403 - Forbidden (no access)")
        else:
            print(f"  ✗ Error: {error_str[:100]}")
