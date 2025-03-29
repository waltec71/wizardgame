init -7 python:
    # Enhanced Story generation logic with memory integration
    
    class EnhancedStoryGenerator:
        """
        Enhanced story generator that utilizes the memory system.
        """
        
        @staticmethod
        def generate_story(player_choice, current_location=None, present_npcs=None, active_quests=None):
            """
            Generates the next part of the story based on memory context and player choice
            
            Args:
                player_choice (str): The player's most recent choice
                current_location (str): Current location in game
                present_npcs (list): NPCs present in the current scene
                active_quests (list): Currently active quests
                
            Returns:
                tuple: (story_text, choices) where:
                    - story_text (str): Generated narrative text
                    - choices (list): List of choices for the player
            """
            try:
                # Get relevant memories as context
                memory_context = memory_system.build_context(
                    current_location=current_location,
                    present_npcs=present_npcs,
                    active_quests=active_quests
                )
                
                # Construct the prompt for story generation
                prompt = f"""You are an AI storyteller for a dark fantasy wizard game.
                
                Current game state:
                {memory_context}
                
                Current location: {current_location or "Unknown"}
                
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
                if USE_TEST_MODE:
                    return TestStoryGenerator.generate_story_test(memory_context, player_choice)
                
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
                
                # Extract and save memories from this story segment
                MemoryManager.use_ai_to_extract_memories(
                    story_part, 
                    player_choice,
                    current_location
                )
                
                return story_part, choices
                
            except Exception as e:
                # Fallback in case of errors
                log_exception("story generation", e, f"player_choice: {player_choice}")
                return f"The ancient tome's pages blur before your eyes. (Error: {str(e)})", ["Continue cautiously"]


    # Test version for development/testing without API calls
    class TestStoryGenerator:
        """
        A test version of the story generator that works without API calls.
        Includes integration with the memory system.
        """
        
        @staticmethod
        def generate_story_test(memory_context, player_choice):
            """
            Generates test stories based on player choice and memory context
            
            Args:
                memory_context (str): Context built from memory system
                player_choice (str): The player's most recent choice
                
            Returns:
                tuple: (story_text, choices)
            """
            print(f"Memory context: {memory_context}")
            
            if "start the game" in player_choice.lower():
                story = "You stand in the dimly lit chamber of the tower. Ancient tomes line the walls, and magical artifacts glow with an eerie light. Your master left you here to study, but you sense something is not right. The air feels heavy with arcane energy."
                choices = ["Examine the tomes", "Investigate the strange glow", "Leave the chamber"]
                
                # Add this as a memory
                memory_system.add_memory(
                    "Your master left you alone in the tower to study.",
                    tags=["Plot", "Character"],
                    related_entities=["Player", "Master", "Tower of Shadows"]
                )
                
            elif "examine the tomes" in player_choice.lower():
                story = "You approach the ancient shelves, your fingers tracing the spines of dusty grimoires. One book seems to pulse with a subtle energy, its leather binding warm to the touch. The title reads 'Whispers of the Void' in a script that seems to shift as you look at it."
                choices = ["Open 'Whispers of the Void'", "Look for other interesting books", "Step away from the shelves"]
                
                memory_system.add_memory(
                    "You found a book called 'Whispers of the Void' that pulses with energy.",
                    tags=["Discovery", "Item"],
                    related_entities=["Whispers of the Void", "Tower of Shadows"]
                )
                
            elif "investigate the strange glow" in player_choice.lower():
                story = "You move toward the source of the ethereal light. A crystal orb sits on a pedestal in the corner, swirling with blue-green energy. As you approach, the light intensifies, and whispers fill your mind—unintelligible yet somehow familiar."
                choices = ["Touch the orb", "Try to understand the whispers", "Return to the center of the room"]
                
                memory_system.add_memory(
                    "There is a crystal orb in the tower that whispers to you.",
                    tags=["Discovery", "Item", "Critical"],
                    related_entities=["Crystal Orb", "Tower of Shadows"]
                )
                
            else:
                story = f"You decided to {player_choice}. The tower seems to respond to your choices, shifting slightly. You feel your powers growing, but also sense that the path you're on will have consequences."
                choices = ["Continue exploring", "Try casting a spell", "Look for hidden passages"]
                
                memory_system.add_memory(
                    f"You chose to {player_choice}.",
                    tags=["Action", "Player"],
                    related_entities=["Player"]
                )
            
            # Save memories to persistent
            memory_system.save_to_file()
            
            return story, choices

    def chunk_story_text(text, max_chars_per_chunk=150):
        """
        Split a story text into smaller, readable chunks
        
        Args:
            text (str): The full story text
            max_chars_per_chunk (int): Maximum characters per chunk
            
        Returns:
            list: List of text chunks
        """
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If the sentence itself exceeds the limit, make it its own chunk
            if len(sentence) >= max_chars_per_chunk:
                # First add any accumulated text as its own chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # Add the long sentence as its own chunk
                chunks.append(sentence.strip())
                continue
            
            # If adding this sentence would exceed the limit, start a new chunk
            if current_chunk and len(current_chunk) + len(sentence) + 1 > max_chars_per_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Otherwise add to the current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if there's anything left
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks