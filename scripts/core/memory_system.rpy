init -10 python:
    import json
    import re
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    class Memory:
        """
        Represents a single memory entry in the game.
        Uses game turns to track when memories were created.
        """
        def __init__(self, content, tags=None, related_entities=None, turn=None):
            """
            Initialize a new memory.
            
            Args:
                content (str): The memory content text
                tags (list): List of tags categorizing the memory
                related_entities (list): Names of entities related to this memory
                turn (int): The game turn when this memory was created
            """
            self.content = content
            self.tags = tags or []
            self.related_entities = related_entities or []
            self.turn = turn or 1  # Default to turn 1 if none provided
            self.access_count = 0  # Track how often this memory is accessed
            self._hash = hash(self.content)  # Create a hash for comparison
            
            # For relationship tracking
            self.related_memories = set()  # Other memories this one relates to
            self.relationship_types = {}   # Map of memory_id -> relationship type
        
        def add_relationship(self, other_memory, relationship_type="related"):
            """
            Create a relationship between this memory and another.
            
            Args:
                other_memory (Memory): The memory to relate to
                relationship_type (str): Type of relationship (e.g., "causes", "contradicts")
            """
            if other_memory is not self:  # Avoid self-relationships
                self.related_memories.add(other_memory)
                self.relationship_types[other_memory._hash] = relationship_type
                
                # Add reciprocal relationship if appropriate
                if relationship_type == "related":
                    other_memory.related_memories.add(self)
                    other_memory.relationship_types[self._hash] = "related"
                elif relationship_type == "causes":
                    other_memory.related_memories.add(self)
                    other_memory.relationship_types[self._hash] = "caused_by"
                elif relationship_type == "contradicts":
                    other_memory.related_memories.add(self)
                    other_memory.relationship_types[self._hash] = "contradicted_by"
        
        def to_dict(self):
            """Convert memory to dictionary for serialization"""
            return {
                "content": self.content,
                "tags": self.tags,
                "related_entities": self.related_entities,
                "turn": self.turn,
                "access_count": self.access_count,
                "relationships": [(mem._hash, self.relationship_types[mem._hash]) 
                                for mem in self.related_memories if mem._hash in self.relationship_types]
            }
        
        @classmethod
        def from_dict(cls, data):
            """Create memory from dictionary"""
            memory = cls(
                content=data["content"],
                tags=data["tags"],
                related_entities=data["related_entities"],
                turn=data.get("turn", 1)
            )
            
            memory.access_count = data.get("access_count", 0)
            # Relationships are reconstructed after all memories are loaded
            return memory
            
        def __str__(self):
            return self.content
            
        def __eq__(self, other):
            """Define equality based on content"""
            if not isinstance(other, Memory):
                return False
            return self.content == other.content
            
        def __hash__(self):
            """Allow using memories in sets"""
            return self._hash
            
        # These methods define comparison to use turns instead of timestamps
        def __lt__(self, other):
            """Less than comparison based on turn"""
            if not isinstance(other, Memory):
                return NotImplemented
            return self.turn < other.turn
            
        def __le__(self, other):
            """Less than or equal comparison based on turn"""
            if not isinstance(other, Memory):
                return NotImplemented
            return self.turn <= other.turn
            
        def __gt__(self, other):
            """Greater than comparison based on turn"""
            if not isinstance(other, Memory):
                return NotImplemented
            return self.turn > other.turn
            
        def __ge__(self, other):
            """Greater than or equal comparison based on turn"""
            if not isinstance(other, Memory):
                return NotImplemented
            return self.turn >= other.turn


    class MemorySystem:
        """
        Manages the storage, retrieval, and maintenance of game memories.
        Enhanced with relationship tracking, memory compression, and forgetting mechanisms.
        """
        def __init__(self):
            self.memories = []
            self.entity_index = defaultdict(list)  # For quick lookup by entity
            self.tag_index = defaultdict(list)     # For quick lookup by tag
            self.hash_index = {}                  # For quick lookup by hash
        
        def add_memory(self, content, tags=None, related_entities=None, turn=None):
            """
            Add a new memory to the system.
            
            Args:
                content (str): The memory content
                tags (list): Tags for categorization (e.g., "Critical", "Character", "Location")
                related_entities (list): Entities mentioned in the memory
                turn (int): The game turn when this memory was created
                
            Returns:
                Memory: The created memory object
            """
            # Use current game turn if none provided
            if turn is None:
                global game_turn
                turn = game_turn
                
            # Create the memory
            memory = Memory(content, tags, related_entities, turn)
            
            # Add to main list
            self.memories.append(memory)
            
            # Update indexes for fast retrieval
            for entity in memory.related_entities:
                self.entity_index[entity.lower()].append(memory)
                
            for tag in memory.tags:
                self.tag_index[tag.lower()].append(memory)
            
            # Store in hash index for relationship reconstruction
            self.hash_index[memory._hash] = memory
                
            return memory
        
        def get_memories_by_tag(self, tag):
            """Get all memories with a specific tag"""
            return self.tag_index.get(tag.lower(), [])
        
        def get_memories_by_entity(self, entity):
            """Get all memories related to a specific entity"""
            return self.entity_index.get(entity.lower(), [])
            
        def get_memories_by_tags(self, tags, require_all=False):
            """
            Get memories matching the given tags.
            
            Args:
                tags (list): List of tags to match
                require_all (bool): If True, memory must have all tags. If False, any match works.
            
            Returns:
                list: Matching memories
            """
            if not tags:
                return []
                
            if require_all:
                # Start with memories that have the first tag
                result = set(self.get_memories_by_tag(tags[0]))
                # Intersect with memories that have each additional tag
                for tag in tags[1:]:
                    result.intersection_update(self.get_memories_by_tag(tag))
                return list(result)
            else:
                # Union all memories with any of the tags
                result = set()
                for tag in tags:
                    result.update(self.get_memories_by_tag(tag))
                return list(result)
        
        def get_recent_memories(self, count=5):
            """Get the most recent memories"""
            return sorted(self.memories, key=lambda m: m.turn, reverse=True)[:count]
        
        def build_context(self, current_location=None, present_npcs=None, active_quests=None, max_tokens=1000):
            """
            Build a relevant context from memories for the current game state.
            Enhanced with better scoring and summarization.
            
            Args:
                current_location (str): The current location name
                present_npcs (list): NPCs present in the current scene
                active_quests (list): Currently active quests
                max_tokens (int): Approximate token limit for context
                
            Returns:
                str: Formatted context for the AI
            """
            context_elements = []
            
            # Always include critical memories
            critical_memories = self.get_memories_by_tag("Critical")
            context_elements.extend(critical_memories)
            
            # Add location-specific memories
            if current_location:
                location_memories = self.get_memories_by_entity(current_location)
                context_elements.extend(location_memories)
            
            # Add character-specific memories for present NPCs
            if present_npcs:
                for npc in present_npcs:
                    npc_memories = self.get_memories_by_entity(npc)
                    context_elements.extend(npc_memories)
            
            # Add quest-related memories
            if active_quests:
                for quest in active_quests:
                    quest_memories = self.get_memories_by_entity(quest)
                    context_elements.extend(quest_memories)
            
            # Add recent important memories
            recent_memories = [m for m in self.get_recent_memories(10) 
                            if "Minor" not in m.tags and m not in context_elements]
            context_elements.extend(recent_memories[:3])  # Add top 3 recent memories
            
            # Remove duplicates while preserving order
            unique_elements = []
            seen = set()
            for memory in context_elements:
                if memory not in seen:
                    seen.add(memory)
                    unique_elements.append(memory)
            
            # Score and sort memories by relevance
            scored_memories = [(self._score_memory_relevance(memory, current_location, present_npcs, active_quests), memory) 
                            for memory in unique_elements]
            scored_memories.sort(reverse=True)  # Sort by score, highest first
            
            # Check if we need compression
            selected_memories = []
            total_length = 0
            for _, memory in scored_memories:
                # Rough token estimation (~4 chars per token)
                memory_length = len(memory.content)
                if total_length + memory_length > max_tokens * 3:  # Leave room for formatting
                    break
                selected_memories.append(memory)
                total_length += memory_length
                
                # Increment access count for this memory
                memory.access_count += 1
            
            # Apply compression if we still have too many memories
            if total_length > max_tokens * 3.5:
                selected_memories = self.compress_memories(selected_memories)
            
            # Format the context
            formatted_context = self._format_context(selected_memories)
            return formatted_context
        
        def _score_memory_relevance(self, memory, current_location, present_npcs, active_quests):
            """
            Enhanced scoring function for memory relevance with turn-based scoring
            
            Args:
                memory (Memory): The memory to score
                current_location (str): Current game location
                present_npcs (list): NPCs in the current scene
                active_quests (list): Active quests
                
            Returns:
                float: Relevance score
            """
            score = 0
            
            # Critical memories always get high score
            if "Critical" in memory.tags:
                score += 10
            
            # Recent memories are more relevant (turn-based recency)
            global game_turn
            turns_ago = game_turn - memory.turn
            recency_score = max(0, 10 - (turns_ago * 0.5))  # Gradually decay over 20 turns
            score += recency_score
                
            # Location relevance
            if current_location:
                if current_location.lower() in [e.lower() for e in memory.related_entities]:
                    score += 4
                # We could add location relationship check here with a location_is_related function
            
            # NPC relevance with priority for directly mentioned NPCs
            if present_npcs:
                for npc in present_npcs:
                    if npc.lower() in [e.lower() for e in memory.related_entities]:
                        score += 3
                        # Give bonus for memories that directly involve current NPCs
                        if any(npc.lower() in m.content.lower() for m in memory.related_memories):
                            score += 1
            
            # Quest relevance with higher scores for active quests
            if active_quests:
                for quest in active_quests:
                    if quest.lower() in [e.lower() for e in memory.related_entities]:
                        score += 5
                        
                        # Give bonus for memories related to uncompleted quest steps
                        if "Incomplete" in memory.tags or "Task" in memory.tags:
                            score += 2
            
            # Tag importance - more detailed scoring based on tag type
            tag_scores = {
                "major": 3,
                "plot": 4,
                "character": 2,
                "location": 2,
                "item": 1,
                "discovery": 3,
                "achievement": 2,
                "decision": 3,
                "minor": -1
            }
            
            for tag in memory.tags:
                tag_lower = tag.lower()
                if tag_lower in tag_scores:
                    score += tag_scores[tag_lower]
            
            # Access count - memories that have been recalled often are important
            score += min(memory.access_count, 5) * 0.5
            
            # Relationship bonus - memories that connect to many others are important
            if memory.related_memories:
                relationship_score = min(len(memory.related_memories), 3) * 0.5
                score += relationship_score
            
            return score
        
        def compress_memories(self, memories, max_length=500):
            """
            Compress a set of related memories into a concise summary.
            
            Args:
                memories (list): List of Memory objects to compress
                max_length (int): Target maximum length for the summary
                
            Returns:
                list: Compressed list of memories
            """
            if not memories or len(memories) <= 2:
                return memories
            
            # Group by related entities
            entity_groups = defaultdict(list)
            for memory in memories:
                for entity in memory.related_entities:
                    entity_groups[entity].append(memory)
            
            # Find predominant entities (those with multiple memories)
            main_entities = [e for e, mems in entity_groups.items() if len(mems) > 2]
            
            # Create summaries for entity groups
            summaries = []
            compressed_memories = set()
            
            for entity in main_entities:
                entity_memories = sorted(entity_groups[entity])
                if len(entity_memories) >= 3:
                    # Create a summary for this entity
                    content = f"Regarding {entity}: "
                    memory_contents = []
                    
                    # Sort by turn
                    entity_memories.sort()
                    
                    for m in entity_memories[:3]:
                        memory_contents.append(m.content)
                        compressed_memories.add(m)
                        
                    content += " ".join(memory_contents)
                    if len(entity_memories) > 3:
                        content += f" ...and {len(entity_memories)-3} more related events."
                    
                    # Collect all unique tags from the memories
                    all_tags = ["Summary"]
                    for m in entity_memories:
                        for tag in m.tags:
                            if tag not in all_tags:
                                all_tags.append(tag)
                    
                    # Create a new memory with the summary
                    summary = Memory(
                        content=content,
                        tags=all_tags,
                        related_entities=[entity],
                        turn=entity_memories[-1].turn  # Use the latest turn
                    )
                    
                    # Add relationships to the original memories
                    for m in entity_memories:
                        summary.add_relationship(m, "summarizes")
                        
                    summaries.append(summary)
            
            # Replace compressed memories with summaries
            result = [m for m in memories if m not in compressed_memories]
            result.extend(summaries)
            
            return result
        
        def _format_context(self, memories):
            """
            Format a list of memories into a coherent context string.
            Enhanced with better organization by type.
            """
            if not memories:
                return "No relevant memories."
            
            # Group memories by type
            character_memories = [m for m in memories if "Character" in m.tags]
            plot_memories = [m for m in memories if "Plot" in m.tags]
            location_memories = [m for m in memories if "Location" in m.tags]
            quest_memories = [m for m in memories if "Quest" in m.tags]
            summary_memories = [m for m in memories if "Summary" in m.tags]
            other_memories = [m for m in memories if not any(t in m.tags for t in ["Character", "Plot", "Location", "Quest", "Summary"])]
            
            formatted = []
            
            # Add summaries first
            if summary_memories:
                formatted.append("Memory Summaries:")
                for memory in summary_memories:
                    formatted.append(f"- {memory.content}")
                formatted.append("")
            
            if plot_memories:
                formatted.append("Important plot events:")
                for memory in plot_memories:
                    formatted.append(f"- {memory.content}")
                formatted.append("")
            
            if character_memories:
                formatted.append("Character information:")
                for memory in character_memories:
                    formatted.append(f"- {memory.content}")
                formatted.append("")
            
            if location_memories:
                formatted.append("Location knowledge:")
                for memory in location_memories:
                    formatted.append(f"- {memory.content}")
                formatted.append("")
                
            if quest_memories:
                formatted.append("Quest information:")
                for memory in quest_memories:
                    formatted.append(f"- {memory.content}")
                formatted.append("")
            
            if other_memories:
                formatted.append("Other memories:")
                for memory in other_memories:
                    formatted.append(f"- {memory.content}")
            
            return "\n".join(formatted)
        
        def prune_memories(self, max_minor_memories=50):
            """
            Remove less important memories to prevent context bloat.
            Uses turn-based scoring to determine which memories to keep.
            
            Args:
                max_minor_memories (int): Maximum number of minor memories to keep
                
            Returns:
                int: Number of memories pruned
            """
            # Only prune memories tagged as Minor
            minor_memories = [m for m in self.memories if "Minor" in m.tags]
            
            if len(minor_memories) <= max_minor_memories:
                return 0
            
            # Sort by turn-based relevance score
            scored_memories = [(self._simplified_score(m), m) for m in minor_memories]
            scored_memories.sort()  # Lowest scores first
            
            # Determine how many to remove
            to_remove = len(minor_memories) - max_minor_memories
            
            # Remove the lowest-scored memories
            removed = 0
            for _, memory in scored_memories[:to_remove]:
                self.memories.remove(memory)
                
                # Also remove from indexes
                for entity in memory.related_entities:
                    if memory in self.entity_index[entity.lower()]:
                        self.entity_index[entity.lower()].remove(memory)
                        
                for tag in memory.tags:
                    if memory in self.tag_index[tag.lower()]:
                        self.tag_index[tag.lower()].remove(memory)
                        
                # Remove from hash index
                if memory._hash in self.hash_index:
                    del self.hash_index[memory._hash]
                    
                removed += 1
            
            return removed

        def _simplified_score(self, memory):
            """Simplified scoring for memory pruning"""
            score = 0
            
            # Critical memories get high score
            if "Critical" in memory.tags:
                score += 100
                
            # Recency bonus based on turns
            global game_turn
            turns_ago = game_turn - memory.turn
            score += max(0, 30 - turns_ago)
            
            # Access count bonus
            score += memory.access_count * 5
            
            # Relationship bonus (memories with many relations are important)
            score += len(memory.related_memories) * 3
            
            return score
        
        def find_conflicting_memories(self):
            """
            Identify potentially conflicting memories based on content similarity.
            
            Returns:
                list: Pairs of potentially conflicting memories
            """
            conflicts = []
            
            # Group memories by entities for efficiency
            for entity, memories in self.entity_index.items():
                if len(memories) < 2:
                    continue
                    
                # Check each pair
                for i, mem1 in enumerate(memories):
                    for mem2 in memories[i+1:]:
                        # Skip if already in a relationship
                        if mem2 in mem1.related_memories:
                            continue
                            
                        # Simple similarity check
                        similarity = self._calculate_text_similarity(mem1.content, mem2.content)
                        if similarity > 0.6:  # Threshold for potential conflict
                            conflicts.append((mem1, mem2, similarity))
            
            return conflicts

        def _calculate_text_similarity(self, text1, text2):
            """
            Calculate similarity between two text strings (simple implementation).
            Uses a word overlap approach.
            """
            # Simple word overlap
            words1 = set(re.findall(r'\w+', text1.lower()))
            words2 = set(re.findall(r'\w+', text2.lower()))
            
            if not words1 or not words2:
                return 0
                
            overlap = len(words1.intersection(words2))
            return overlap / min(len(words1), len(words2))
        
        def analyze_text_for_memories(self, text, entities=None):
            """
            Analyze text to identify potential memories with appropriate tags.
            This is helpful for automatically processing story text.
            
            Args:
                text (str): Text to analyze
                entities (list): Known entities that might be referenced
                
            Returns:
                list: List of potential Memory objects
            """
            # This is a simplified version - in a real game, you might want to use the API
            # to help analyze text for important memories
            potential_memories = []
            
            # Look for sentences that might be important
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            for sentence in sentences:
                # Skip short sentences
                if len(sentence) < 15:
                    continue
                    
                # Determine tags and entities
                tags = []
                related_entities = []
                
                # Check for known entities
                if entities:
                    for entity in entities:
                        if entity and entity.lower() in sentence.lower():
                            related_entities.append(entity)
                
                # Enhanced heuristics for tagging
                if any(word in sentence.lower() for word in ["discover", "found", "revealed", "secret", "hidden"]):
                    tags.append("Discovery")
                    
                if any(word in sentence.lower() for word in ["quest", "mission", "task", "objective"]):
                    tags.append("Quest")
                    
                if re.search(r'(?i)you (gain|earned|learned|acquired|received|got|have)', sentence):
                    tags.append("Acquisition")
                    
                if any(word in sentence.lower() for word in ["critical", "important", "essential", "key", "vital"]):
                    tags.append("Critical")
                    
                # New patterns for improved auto-tagging
                if re.search(r'(?i)(kill|defeat|vanquish|destroy|overcome)', sentence):
                    tags.append("Combat")
                    
                if re.search(r'(?i)(promise|vow|swear|pledge)', sentence):
                    tags.append("Commitment")
                    
                if re.search(r'(?i)(betray|deceive|trick|lie)', sentence):
                    tags.append("Deception")
                
                # Only add if we have some tags or entities
                if tags or related_entities:
                    potential_memories.append({
                        "content": sentence,
                        "tags": tags,
                        "related_entities": related_entities
                    })
            
            return potential_memories
            
        def reconstruct_relationships(self):
            """
            Reconstruct memory relationships after loading from saved game.
            This rebuilds the relationship links between memory objects.
            """
            # Process each memory
            for memory in self.memories:
                # Skip memories with no relationships data
                if not hasattr(memory, "relationships") or not memory.relationships:
                    continue
                    
                # Rebuild relationships
                for related_hash, rel_type in memory.relationships:
                    if related_hash in self.hash_index:
                        related_memory = self.hash_index[related_hash]
                        memory.add_relationship(related_memory, rel_type)
        
        # Save and load functions
        def save_to_file(self):
            """Save memories to game variable instead of persistent storage"""
            global stored_memory_data
            stored_memory_data = [memory.to_dict() for memory in self.memories]
        
        def load_from_file(self):
            """Load memories from game variable instead of persistent storage"""
            global stored_memory_data
            if stored_memory_data:
                try:
                    self.memories = [Memory.from_dict(data) for data in stored_memory_data]
                    
                    # Rebuild indexes
                    self.entity_index = defaultdict(list)
                    self.tag_index = defaultdict(list)
                    self.hash_index = {}
                    
                    for memory in self.memories:
                        for entity in memory.related_entities:
                            self.entity_index[entity.lower()].append(memory)
                        for tag in memory.tags:
                            self.tag_index[tag.lower()].append(memory)
                        self.hash_index[memory._hash] = memory
                        
                    # Reconstruct relationships between memories
                    self.reconstruct_relationships()
                    
                except Exception as e:
                    log_exception("story generation", e, f"player_choice: {player_choice}")
                    print(f"Error loading memories: {str(e)}")
    
    
    # Initialize the memory system
    memory_system = MemorySystem()

    # Add initial memories on first load if needed
    def initialize_starting_memories():
        if not memory_system.memories:
            memory_system.add_memory(
                "You are a novice wizard who has just begun arcane studies.",
                tags=["Character", "Critical"],
                related_entities=["Player"]
            )
            memory_system.add_memory(
                "Your studies take place in the Tower of Shadows.",
                tags=["Location", "Critical"],
                related_entities=["Tower of Shadows"]
            )
    
    # Helper function for the story generator to use
    def get_relevant_context(current_location=None, present_npcs=None, active_quests=None):
        """Build and return relevant memory context for the current scene."""
        return memory_system.build_context(current_location, present_npcs, active_quests)