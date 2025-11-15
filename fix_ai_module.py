import os
import sys
import traceback
from pathlib import Path

# Find the AI module file
def find_ai_file():
    possible_paths = [
        'finucity/ai.py',
        'finucity/ai/__init__.py',
        'ai.py',
        'finucity/services/ai.py'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found AI module at: {path}")
            return path
    
    # If not found in common locations, search for ai.py files
    ai_files = list(Path('.').rglob('ai.py'))
    if ai_files:
        print(f"Found AI module at: {ai_files[0]}")
        return str(ai_files[0])
    
    return None

# Read the current AI file
ai_file_path = find_ai_file()
if not ai_file_path:
    print("Could not find the AI module file")
    sys.exit(1)

# Backup the original file
backup_path = f"{ai_file_path}.backup"
with open(ai_file_path, 'r') as f:
    original_content = f.read()

with open(backup_path, 'w') as f:
    f.write(original_content)
    print(f"Backed up original AI module to {backup_path}")

# Check if the file contains the _call_groq_api method
if "_call_groq_api" in original_content:
    print("Found _call_groq_api method in the AI module")
    
    # Create a debug version of the method to print API interactions
    debug_method = """
    def _call_groq_api(self, question: str, category: str, context: Dict) -> Dict[str, Any]:
        \"\"\"Call Groq API with proper error handling and debugging\"\"\"
        try:
            # Build the system prompt
            system_prompt = self._build_system_prompt(category, context)
            
            # Build the user message with context
            user_message = self._build_user_message(question, context)
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False
            }
            
            # Add conversation history if available
            if context.get('user_history'):
                history_messages = context['user_history'][-6:]  # Last 6 messages
                # Insert history before user message
                payload["messages"] = [
                    {"role": "system", "content": system_prompt}
                ] + history_messages + [
                    {"role": "user", "content": user_message}
                ]
            
            # Debug prints
            print(f"\\n==== GROQ API REQUEST ====")
            print(f"Model: {self.model_name}")
            print(f"Headers: {headers}")
            print(f"Payload (partial): {{'model': {payload['model']}, 'temperature': {payload['temperature']}, 'max_tokens': {payload['max_tokens']}}}")
            print(f"System prompt: {system_prompt[:100]}...")
            print(f"User message: {user_message[:100]}...")
            
            # Make API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                ai_content = result['choices'][0]['message']['content']
                
                print(f"\\n==== GROQ API SUCCESS ====")
                print(f"Status code: {response.status_code}")
                print(f"Response preview: {ai_content[:100]}...")
                
                return {
                    'success': True,
                    'response': ai_content.strip(),
                    'model_used': self.model_name,
                    'tokens_used': result.get('usage', {}).get('total_tokens', 0)
                }
            else:
                error_msg = f"Groq API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error'].get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                print(f"\\n==== GROQ API ERROR ====")
                print(f"Status code: {response.status_code}")
                print(f"Error message: {error_msg}")
                print(f"Response text: {response.text[:200]}...")
                
                return self._generate_fallback_response(question, category, error_msg)
                
        except requests.exceptions.Timeout:
            print("❌ Groq API timeout")
            return self._generate_fallback_response(question, category, "API timeout")
        except requests.exceptions.ConnectionError:
            print("❌ Groq API connection error")
            return self._generate_fallback_response(question, category, "Connection error")
        except Exception as e:
            print(f"❌ Groq API call error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return self._generate_fallback_response(question, category, str(e))
    """
    
    # Replace the original method with the debug version
    modified_content = original_content.replace("def _call_groq_api", debug_method)
    
    # Write the modified content back to the file
    with open(ai_file_path, 'w') as f:
        f.write(modified_content)
        print("Added debug logging to _call_groq_api method")
else:
    print("Could not find _call_groq_api method in the AI module")
    print("Manual inspection needed")

print("\nAI module has been updated with debug logging")
print("Run your application again to see detailed API interaction logs")