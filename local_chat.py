import requests
import json
import time
from config import LOCAL_AI_URL


class LocalChat:
    def __init__(self):
        self.conversation_history = []
        self.local_ai_url = LOCAL_AI_URL or "http://0.0.0.0:8001/v1/chat/completions"
        
        # System prompt for local AI
        self.system_prompt = """You are an AI assistant running locally on a mobile device. 
        You are helpful, concise, and respond in a friendly manner.
        Keep responses brief (1-2 sentences when possible)."""
        
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })

    def chat(self, user_message):
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Prepare the request to local AI server
            payload = {
                "model": "local-model",  # This can be adjusted based on your model
                "messages": self.conversation_history,
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": False
            }
            
            response = requests.post(
                self.local_ai_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # Add AI response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                return ai_response
            else:
                print(f"Error from local AI server: {response.status_code} - {response.text}")
                return "Sorry, I couldn't get a response from the local AI server."
                
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to local AI server. Please make sure it's running on your phone."
        except requests.exceptions.Timeout:
            return "Error: Local AI server request timed out."
        except Exception as e:
            print(f"Error in local chat: {e}")
            return "Sorry, there was an error communicating with the local AI."