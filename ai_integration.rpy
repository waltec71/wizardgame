init python:
    import requests
    import json
    import time
    
    # Configuration
    #api key auto-pulled from secrets.rpy
    model = "gemini-2.0-flash"  # Changed to a more standard model name
    API_URL = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={API_KEY}"
    
    # Function to call the AI API
    def generate_story(context, player_choice):
        try:
            # Construct your prompt
            prompt = f"""You are an AI storyteller for a dark fantasy wizard game.
            
            Previous context:
            {context}
            
            Player's choice:
            {player_choice}
            
            Generate the next part of the story (1-2 paragraphs) and provide 2-4 choices for the player depending on what makes sense for the situation.
            - For simple decisions: provide 2 choices
            - For complex decisions with multiple approaches: provide 3 choices
            - Only when there are distinct pathways or special opportunities: provide 4 choices
            Format your response exactly as follows:
            STORY: [story text here]
            CHOICES:
            1. [first choice]
            2. [second choice]
            3. [third choice (if appropriate)]
            4. [fourth choice (if appropriate)]
            """
            
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
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            }
            
            # Make the API call
            response = requests.post(API_URL, headers=headers, json=data)
            result = json.loads(response.text)
            
            # Extract the AI's response - corrected path to access response data
            ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse response
            story_part = ai_response.split("STORY:")[1].split("CHOICES:")[0].strip()
            choices_part = ai_response.split("CHOICES:")[1].strip().split("\n")
            choices = [choice.strip()[2:].strip() for choice in choices_part if choice.strip()]

            #in case the AI did not return any choices
            if not choices:
                choices = ["Continue"]

            return story_part, choices
            
        except Exception as e:
            # Fallback in case of errors
            return f"The ancient tome's pages blur before your eyes. (Error: {str(e)})", ["Continue cautiously"]

    #test story generator
    def generate_story_test(context, player_choice):
        if "start the game" in player_choice.lower():
            return "You stand in the dimly lit chamber of the tower. Ancient tomes line the walls, and magical artifacts glow with an eerie light. Your master left you here to study, but you sense something is not right. The air feels heavy with arcane energy.", ["Examine the tomes", "Investigate the strange glow", "Leave the chamber"]
        else:
            return f"You decided to {player_choice}. The tower seems to respond to your choices, shifting slightly. You feel your powers growing.", ["Continue exploring", "Try casting a spell", "Look for hidden passages"]