init -11 python:
    import requests
    import json
    import time
    import os
    from datetime import datetime
    
    # API Configuration
    model = "gemini-2.0-flash"  # Model configuration
    API_URL = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={API_KEY}"
    
    # Create logs directory
    if not os.path.exists(os.path.join(config.basedir, "game/logs")):
        try:
            os.makedirs(os.path.join(config.basedir, "game/logs"))
        except:
            pass  # Ignore if we can't create the directory
    
    # Simple log function
    def log_api_interaction(prompt, response=None, error=None):
        """
        Logs an API interaction to a file
        
        Args:
            prompt (str): The prompt sent to the API
            response (str): The response received (optional)
            error (str): Any error that occurred (optional)
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file = os.path.join(config.basedir, "game/logs/api_log.txt")
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}]\n")
                f.write("PROMPT:\n")
                f.write(f"{prompt}\n\n")
                
                if response:
                    f.write("RESPONSE:\n")
                    f.write(f"{response}\n\n")
                
                if error:
                    f.write("ERROR:\n")
                    f.write(f"{error}\n\n")
                
                f.write("-" * 80 + "\n\n")
                
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
    
    class APIHandler:
        """
        Handles all API interactions for the game.
        This class centralizes API call logic to make it easy to add new AI request types.
        """
        
        @staticmethod
        def call_api(prompt, temperature=0.7, max_tokens=1000):
            """
            Makes a generic API call to the LLM service
            
            Args:
                prompt (str): The prompt to send to the API
                temperature (float): Controls randomness (0.0-1.0)
                max_tokens (int): Maximum output length
                
            Returns:
                str: The API response text or error message
            """
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                
                data = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens
                    }
                }
                
                # Make the API call
                response = requests.post(API_URL, headers=headers, json=data)
                
                # Check for successful response
                if response.status_code != 200:
                    error_msg = f"API Error (Status Code: {response.status_code}): {response.text}"
                    # Log the error
                    log_api_interaction(prompt, error=error_msg)
                    return error_msg
                
                # Parse the response
                result = json.loads(response.text)
                response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Log the successful interaction (both prompt and response)
                log_api_interaction(prompt, response=response_text)
                
                return response_text
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                # Log the exception
                log_api_interaction(prompt, error=error_msg)
                return error_msg
    
    # Placeholder for additional API handlers as the project expands
    # For example:
    # def call_image_generation_api(prompt):
    #     # Image generation API call
    #     pass
    
    # def call_audio_generation_api(prompt):
    #     # Audio generation API call
    #     pass