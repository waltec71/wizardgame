init -8 python:
    class MemoryManager:
        """
        Handles the integration between the story generator and memory system.
        Enhanced with improved extraction, relationship tracking, and conflict resolution.
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
            
            # Save to file
            memory_system.save_to_file()
            
            return saved_memories
        
        @staticmethod
        def use_ai_to_extract_memories(story_text, player_choice, current_location=None, present_npcs=None):
            """
            Use the AI to analyze story text and extract important memories.
            Enhanced with more detailed prompting and relationship handling.
            
            Args:
                story_text (str): The generated story text
                player_choice (str): The player's choice
                current_location (str): Current game location
                present_npcs (list): NPCs present in the scene
                
            Returns:
                list: Memories that were extracted and saved
            """
            # Skip if test mode is active or for very short texts
            if USE_TEST_MODE or len(story_text) < 50:
                return []
                
            prompt = f"""You are an AI analyzing a dark fantasy wizard game story to extract important memories.
    
            Story text:
            "{story_text}"
            
            Player's choice:
            "{player_choice}"
            
            Current location: {current_location or "Unknown"}
            Present NPCs: {", ".join(present_npcs) if present_npcs else "None"}
            
            Please extract ONLY truly significant memories from this text. Focus on:
            1. Plot-critical revelations
            2. Character relationships or development
            3. Discoveries about the world or magic
            4. New quest information
            5. Major player decisions
            
            For each memory:
            1. Express it in a clear, concise sentence
            2. Assign appropriate tags from: Critical, Plot, Character, Location, Item, Discovery, Action, Quest, Decision
            3. List any entities (characters, places, items) mentioned
            
            Format your response as JSON:
            [
                {
                "content": "The concise memory as a single sentence",
                "tags": ["tag1", "tag2"],
                "related_entities": ["entity1", "entity2"],
                "relationships": [{"content": "brief description of another memory this relates to", "type": "causes/related/contradicts"}]
                }
            ]
            
            Important guidelines:
            - Limit to 1-3 memories maximum
            - Focus on SIGNIFICANCE not just what happened
            - Include ONLY information that would affect future story decisions
            - Make related_entities as specific as possible (e.g., 'Tower of Shadows' not just 'tower')
            - Use the relationships field to indicate when one memory relates to another memory (optional)
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
                    
                    # Process relationships if they exist
                    if MEMORY_SYSTEM_FULL_FEATURES:
                        for i, mem_data in enumerate(memory_data):
                            if "relationships" in mem_data and mem_data["relationships"]:
                                # For each relationship
                                for rel in mem_data["relationships"]:
                                    # Try to find a memory that matches the description
                                    matching_memory = None
                                    for existing_mem in memory_system.memories:
                                        # Skip the current memory
                                        if existing_mem == saved_memories[i]:
                                            continue
                                            
                                        # Simple text similarity check
                                        similarity = memory_system._calculate_text_similarity(
                                            rel["content"],
                                            existing_mem.content
                                        )
                                        if similarity > 0.6:  # Reasonable match threshold
                                            matching_memory = existing_mem
                                            break
                                    
                                    # If we found a match, establish the relationship
                                    if matching_memory:
                                        saved_memories[i].add_relationship(
                                            matching_memory,
                                            rel.get("type", "related")
                                        )
                    
                    # Check for and resolve potential conflicts
                    if MEMORY_SYSTEM_FULL_FEATURES:
                        conflicts = memory_system.find_conflicting_memories()
                        for mem1, mem2, similarity in conflicts:
                            # For high similarity, mark as related
                            if similarity > 0.8:
                                mem1.add_relationship(mem2, "related")
                            # For moderately high similarity, check if they might contradict
                            elif similarity > 0.6:
                                # This is just a heuristic - in a complete implementation
                                # you might use the API to analyze if they contradict
                                if any(word in mem1.content.lower() for word in ["not", "never", "no"]):
                                    mem1.add_relationship(mem2, "contradicts")
                    
                    # Save to file
                    memory_system.save_to_file()
                    
                    # Periodically prune memories to prevent bloat
                    if len(memory_system.memories) > 100:
                        memory_system.prune_memories()
                    
                    return saved_memories
                else:
                    # Fallback to basic extraction if JSON parsing fails
                    return MemoryManager.extract_memories_from_story(
                        story_text, player_choice, current_location, present_npcs
                    )
                    
            except Exception as e:
                print(f"Error in AI memory extraction: {str(e)}")
                # Fallback to basic extraction
                return MemoryManager.extract_memories_from_story(
                    story_text, player_choice, current_location, present_npcs
                )
                
        @staticmethod
        def add_relationship_between_memories(memory1_content, memory2_content, relationship_type="related"):
            """
            Create a relationship between two memories based on their content.
            
            Args:
                memory1_content (str): Content of first memory to relate
                memory2_content (str): Content of second memory to relate
                relationship_type (str): Type of relationship
                
            Returns:
                bool: True if relationship was created, False otherwise
            """
            if not MEMORY_SYSTEM_FULL_FEATURES:
                return False
                
            memory1 = None
            memory2 = None
            
            # Find memories by content
            for memory in memory_system.memories:
                # Use partial matching
                if memory1_content in memory.content:
                    memory1 = memory
                if memory2_content in memory.content:
                    memory2 = memory
                    
                # Break if we found both
                if memory1 and memory2:
                    break
            
            # Create relationship if both memories found
            if memory1 and memory2 and memory1 != memory2:
                memory1.add_relationship(memory2, relationship_type)
                return True
                
            return False
            
        @staticmethod
        def summarize_memories_for_entity(entity, max_memories=5):
            """
            Create a summary memory for an entity with multiple related memories.
            
            Args:
                entity (str): The entity to summarize memories for
                max_memories (int): Maximum number of memories to include
                
            Returns:
                Memory: The created summary memory, or None if not enough memories
            """
            if not MEMORY_SYSTEM_FULL_FEATURES:
                return None
                
            # Get memories for this entity
            entity_memories = memory_system.get_memories_by_entity(entity)
            
            # Only summarize if we have enough memories
            if len(entity_memories) < 3:
                return None
                
            # Sort by timestamp (newest first)
            entity_memories.sort(reverse=True)
            
            # Create a summary
            content = f"About {entity}: "
            included_memories = entity_memories[:max_memories]
            
            # Extract key points
            memory_contents = [m.content for m in included_memories]
            content += " ".join(memory_contents)
            
            if len(entity_memories) > max_memories:
                content += f" ...and {len(entity_memories)-max_memories} more related events."
            
            # Create a summary memory
            summary = memory_system.add_memory(
                content=content,
                tags=["Summary"] + list(set().union(*[set(m.tags) for m in included_memories])),
                related_entities=[entity]
            )
            
            # Add relationships to the original memories
            for m in included_memories:
                summary.add_relationship(m, "summarizes")
                
            return summary