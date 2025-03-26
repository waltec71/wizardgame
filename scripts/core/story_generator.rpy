init -9 python:
    # Story generation logic
    
    class StoryGenerator:
        """
        Handles story generation and progression logic.
        Uses the APIHandler to make API calls for narrative content.
        """
        
        @staticmethod
        def generate_story(context, player_choice):
            """
            Generates the next part of the story based on context and player choice
            
            Args:
                context (str): Current game context/state
                player_choice (str): The player's most recent choice
                
            Returns:
                tuple: (story_text, choices) where:
                    - story_text (str): Generated narrative text
                    - choices (list): List of choices for the player
            """
            try:
                # Construct the prompt for story generation
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
                
                # Call the API using the APIHandler
                ai_response = APIHandler.call_api(prompt)
                
                # Check if the response contains an error message
                if ai_response.startswith("Error:") or ai_response.startswith("API Error"):
                    return f"The ancient tome's pages blur before your eyes. {ai_response}", ["Continue cautiously"]
                
                # Parse response
                story_part = ai_response.split("STORY:")[1].split("CHOICES:")[0].strip()
                choices_part = ai_response.split("CHOICES:")[1].strip().split("\n")
                choices = [choice.strip()[2:].strip() for choice in choices_part if choice.strip()]
                
                # Fallback in case the AI did not return any choices
                if not choices:
                    choices = ["Continue"]
                
                return story_part, choices
                
            except Exception as e:
                # Fallback in case of errors
                return f"The ancient tome's pages blur before your eyes. (Error: {str(e)})", ["Continue cautiously"]
    
    # Test version for development/testing without API calls
    class TestStoryGenerator:
        """
        A test version of the story generator that works without API calls.
        Useful for testing game flow without consuming API quota.
        """
        
        @staticmethod
        def generate_story_test(context, player_choice):
            """
            Generates test stories based on player choice
            
            Args:
                context (str): Current game context/state
                player_choice (str): The player's most recent choice
                
            Returns:
                tuple: (story_text, choices)
            """
            if "start the game" in player_choice.lower():
                return "You stand in the dimly lit chamber of the tower. Ancient tomes line the walls, and magical artifacts glow with an eerie light. Your master left you here to study, but you sense something is not right. The air feels heavy with arcane energy.", ["Examine the tomes", "Investigate the strange glow", "Leave the chamber"]
            else:
                return f"You decided to {player_choice}. The tower seems to respond to your choices, shifting slightly. You feel your powers growing.", ["Continue exploring", "Try casting a spell", "Look for hidden passages"]