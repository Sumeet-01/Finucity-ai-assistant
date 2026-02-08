"""
Test GitHub OpenAI API directly
"""
import os
from openai import OpenAI

# Test GitHub OpenAI endpoint
api_key = os.environ.get("GITHUB_TOKEN", "")
api_url = os.environ.get("AI_API_URL", "https://models.github.ai/inference")
model_name = os.environ.get("AI_MODEL_NAME", "gpt-4o-mini")

if not api_key:
    print("ERROR: GITHUB_TOKEN environment variable not set")
    exit(1)

print(f"API Key: {api_key[:20]}...")
print(f"API URL: {api_url}")
print(f"Model: {model_name}")
print("-" * 60)

try:
    client = OpenAI(
        base_url=api_url,
        api_key=api_key,
    )
    
    print("✅ Client created successfully")
    print("🔄 Sending test message...")
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": "What is GST in India?"}
        ],
        model=model_name,
        temperature=0.7,
        max_tokens=150
    )
    
    print("✅ Response received!")
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    print(traceback.format_exc())
