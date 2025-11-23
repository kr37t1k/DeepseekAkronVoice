import requests
import time
import threading
import queue
from config import LOCAL_AI_URL, CONNECTION_TIMEOUT, MAX_RETRIES
from llama_cpp import Llama, llm

class EnhancedLocalChat:
    def __init__(self, model_path=None, max_tokens=512, temperature=0.7, top_p=0.9):
        self.model_path = model_path or "./models/llama-2-7b-chat.Q4_K_M.gguf"  # Default model path
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.conversation_history = []
        self.model = None
        self.load_lock = threading.Lock()
        
        # Initialize the model
        self._load_model()
    
    def _load_model(self):
        """Load the Llama model with error handling"""
        with self.load_lock:
            attempt = 0
            while attempt < MAX_RETRIES:
                try:
                    print(f"🔄 Loading model (attempt {attempt + 1}/{MAX_RETRIES})...")
                    
                    # Try to initialize the model
                    self.model = Llama(
                        model_path=self.model_path,
                        n_ctx=2048,  # Context size
                        n_threads=4,  # Number of threads to use
                        n_gpu_layers=-1,  # Use GPU if available
                        verbose=False  # Reduce logging
                    )
                    
                    print(f"✅ Model loaded successfully from {self.model_path}")
                    return True
                    
                except Exception as e:
                    attempt += 1
                    print(f"⚠️ Error loading model (attempt {attempt}): {e}")
                    
                    if attempt >= MAX_RETRIES:
                        print(f"❌ Failed to load model after {MAX_RETRIES} attempts")
                        # Try fallback initialization with minimal settings
                        try:
                            self.model = Llama(
                                model_path=self.model_path,
                                n_ctx=512,
                                n_threads=2,
                                verbose=False
                            )
                            print("✅ Model loaded with fallback settings")
                            return True
                        except Exception as fallback_error:
                            print(f"❌ Fallback model loading also failed: {fallback_error}")
                            raise fallback_error
                    
                    # Wait before retrying
                    time.sleep(2)
    
    def _prepare_prompt(self, user_input):
        """Prepare the prompt with conversation history"""
        # Create a formatted conversation history
        conversation = ""
        for msg in self.conversation_history[-5:]:  # Use last 5 exchanges
            role = msg['role']
            content = msg['content']
            conversation += f"{role.capitalize()}: {content}\n"
        
        # Add the current user input
        conversation += f"User: {user_input}\nAssistant:"
        
        return conversation
    
    def _handle_model_response(self, response):
        """Process and clean the model response"""
        if hasattr(response, 'choices') and len(response.choices) > 0:
            # OpenAI API format
            content = response.choices[0].message.content
        elif isinstance(response, dict) and 'choices' in response:
            # Dictionary response
            content = response['choices'][0]['message']['content']
        elif hasattr(response, 'text'):
            # Direct text response
            content = response.text
        else:
            # Raw response
            content = str(response)
        
        # Clean the response
        content = content.strip()
        
        # Remove common artifacts
        if content.startswith("Assistant:"):
            content = content[10:].strip()
        
        return content
    
    def chat(self, user_input, stream=False):
        """Main chat method with enhanced error handling"""
        try:
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Prepare the prompt
            prompt = self._prepare_prompt(user_input)
            
            # Generate response with error handling
            response = None
            attempt = 0
            
            while attempt < MAX_RETRIES and response is None:
                try:
                    if stream:
                        # Stream response if requested
                        response = self.model.create_chat_completion(
                            messages=[{"role": "user", "content": user_input}],
                            max_tokens=self.max_tokens,
                            temperature=self.temperature,
                            top_p=self.top_p,
                            stream=True
                        )
                        
                        # Collect streamed response
                        full_response = ""
                        for chunk in response:
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    full_response += delta['content']
                        
                        response = {"choices": [{"message": {"content": full_response}}]}
                    else:
                        # Non-streaming response
                        response = self.model.create_chat_completion(
                            messages=[{"role": "user", "content": user_input}],
                            max_tokens=self.max_tokens,
                            temperature=self.temperature,
                            top_p=self.top_p
                        )
                    
                except Exception as e:
                    attempt += 1
                    print(f"⚠️ Error during generation (attempt {attempt}): {e}")
                    
                    if attempt >= MAX_RETRIES:
                        # Fallback: try with different parameters
                        try:
                            response = self.model.create_chat_completion(
                                messages=[{"role": "user", "content": user_input}],
                                max_tokens=min(self.max_tokens//2, 256),
                                temperature=min(self.temperature + 0.2, 1.0),
                                top_p=1.0
                            )
                        except Exception as fallback_error:
                            print(f"❌ All generation attempts failed: {fallback_error}")
                            return "Sorry, I'm having trouble generating a response right now."
                    
                    time.sleep(1)
            
            # Process the response
            content = self._handle_model_response(response)
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": content})
            
            return content
            
        except Exception as e:
            print(f"❌ Error in chat method: {e}")
            # Return a safe fallback response
            fallback_response = "I apologize, but I encountered an error processing your request. Could you please try again?"
            self.conversation_history.append({"role": "assistant", "content": fallback_response})
            return fallback_response
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
    
    def get_model_info(self):
        """Get information about the loaded model"""
        try:
            if self.model:
                return {
                    "model_path": self.model_path,
                    "context_size": getattr(self.model, 'n_ctx', 'Unknown'),
                    "loaded": True
                }
            else:
                return {"loaded": False}
        except Exception as e:
            return {"error": str(e), "loaded": False}
    
    def change_model(self, new_model_path):
        """Change to a different model"""
        try:
            old_model_path = self.model_path
            self.model_path = new_model_path
            
            # Reload the model
            self._load_model()
            
            print(f"✅ Changed model from {old_model_path} to {new_model_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to change model: {e}")
            # Revert to old model
            self.model_path = old_model_path
            self._load_model()
            return False
    
    def health_check(self):
        """Perform a health check on the model"""
        try:
            test_input = "Hello, how are you?"
            response = self.chat(test_input)
            
            if response and len(response) > 0:
                return {"status": "healthy", "response_length": len(response)}
            else:
                return {"status": "unhealthy", "error": "Empty response"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}