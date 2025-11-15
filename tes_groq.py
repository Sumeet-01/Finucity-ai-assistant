import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("❌ Error: GROQ_API_KEY not found in environment variables")
    exit(1)

print(f"✓ Found API key: {api_key[:5]}...{api_key[-4:]}")

# Test API
try:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",  # Try this model
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, are you working?"}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    print("Sending test request to Groq API...")
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f"\n✓ API Success! Response: \"{content}\"\n")
        print("Your Groq API is working correctly.")
    else:
        print(f"\n❌ API Error: {response.status_code}")
        print(response.text)
        
        if response.status_code == 401:
            print("\n⚠️ Authentication failed. Your API key may be invalid or expired.")
        elif response.status_code == 404:
            print("\n⚠️ Model not found. The model 'llama-3.1-8b-instant' might not be available.")
            # Try with a different model
            print("\nTrying with alternative model 'gemma-7b-it'...")
            payload["model"] = "gemma-7b-it"
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"\n✓ Alternative model works! Response: \"{content}\"\n")
                print("Update your AI_MODEL_NAME in .env to 'gemma-7b-it'")
            else:
                print(f"\n❌ Alternative model also failed: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error connecting to Groq API: {str(e)}")
    print("\nPlease check your internet connection and API key.")