init -11 python:
    import requests
    import json
    import time
    
    # API Configuration
    model = "gemini-2.0-flash"  # Model configuration
    API_URL = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={API_KEY}"
    
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
                    return f"API Error (Status Code: {response.status_code}): {response.text}"
                
                # Parse the response
                result = json.loads(response.text)
                return result["candidates"][0]["content"]["parts"][0]["text"]
                
            except Exception as e:
                return f"Error: {str(e)}"
    
    # Placeholder for additional API handlers as the project expands
    # For example:
    # def call_image_generation_api(prompt):
    #     # Image generation API call
    #     pass
    
    # def call_audio_generation_api(prompt):
    #     # Audio generation API call
    #     pass