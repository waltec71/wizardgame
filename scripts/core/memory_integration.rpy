init -8 python:
    class MemoryManager:
        """
        Handles the integration between the story generator and memory system.
        """
        
        @staticmethod
        def extract_memories_from_story(story_text, player_choice, current_location=None, present_npcs=None):
            """
            Analyze story text to extract and save important memories.
            
            Args:
                story_text (str): The generated story text
                player_choice (str): The player's choice that led to this story
                current_location (str): Current game location
                present_npcs (list): NPCs present in the scene
                
            Returns:
                list: Memories that were extracted and saved
            """
            # Initial simple memory extraction
            potential_memories = memory_system.analyze_text_for_memories(
                story_text, 
                entities=[current_location] + (present_npcs or [])
            )
            
            # Add player choice as a memory if it seems significant
            if len(player_choice) > 10 and not player_choice.startswith("Continue"):
                memory_system.add_memory(
                    f"You chose to {player_choice}.",
                    tags=["Action", "Player", "Recent"],
                    related_entities=["Player"]
                )
            
            # Save extracted memories
            saved_memories = []
            for mem in potential_memories:
                # If we have entities or it seems important, save it
                if mem["related_entities"] or "Critical" in mem["tags"] or "Discovery" in mem["tags"]:
                    memory = memory_system.add_memory(
                        mem["content"],
                        tags=mem["tags"],
                        related_entities=mem["related_entities"]
                    )
                    saved_memories.append(memory)
            
            # Save to persistent storage
            memory_system.save_to_persistent()
            
            return saved_memories
        
        @staticmethod
        def use_ai_to_extract_memories(story_text, player_choice, current_location=None):
            """
            Use the AI to analyze story text and extract important memories.
            More sophisticated than the basic extraction method.
            
            Args:
                story_text (str): The generated story text
                player_choice (str): The player's choice
                current_location (str): Current game location
                
            Returns:
                list: Memories that were extracted and saved
            """
            # Skip if test mode is active or for very short texts
            if USE_TEST_MODE or len(story_text) < 50:
                return []
                
            prompt = f"""You are an AI analyzing story text from a dark fantasy game to extract important memories.
            
            Story text:
            "{story_text}"
            
            Player's choice:
            "{player_choice}"
            
            Current location: {current_location or "Unknown"}
            
            Please identify 1-3 important pieces of information from this text that should be remembered for future reference.
            For each memory:
            1. Extract the key information in a concise sentence
            2. Assign appropriate tags from: Critical, Plot, Character, Location, Item, Discovery, Action, Minor
            3. List any entities (characters, places, items) mentioned
            
            Format your response as JSON:
            [
              {{
                "content": "The extracted memory as a sentence",
                "tags": ["tag1", "tag2"],
                "related_entities": ["entity1", "entity2"]
              }}
            ]
            
            Only include truly important information that would affect future story decisions or character knowledge.
            """
            
            try:
                # Call the API for memory analysis
                ai_response = APIHandler.call_api(prompt, temperature=0.3)
                
                # Extract the JSON part from the response
                json_match = re.search(r'\[\s*\{.*\}\s*\]', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    memory_data = json.loads(json_str)
                    
                    # Save the AI-identified memories
                    saved_memories = []
                    for mem_data in memory_data:
                        memory = memory_system.add_memory(
                            mem_data["content"],
                            tags=mem_data["tags"],
                            related_entities=mem_data["related_entities"]
                        )
                        saved_memories.append(memory)
                    
                    # Save to persistent storage
                    memory_system.save_to_persistent()
                    
                    return saved_memories
                else:
                    # Fallback to basic extraction if JSON parsing fails
                    return MemoryManager.extract_memories_from_story(
                        story_text, player_choice, current_location
                    )
                    
            except Exception as e:
                print(f"Error in AI memory extraction: {str(e)}")
                # Fallback to basic extraction
                return MemoryManager.extract_memories_from_story(
                    story_text, player_choice, current_location
                )