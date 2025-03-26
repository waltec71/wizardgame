init -10 python:
    import json
    import re
    from datetime import datetime
    from collections import defaultdict
    
    class Memory:
        """
        Represents a single memory entry in the game.
        """
        def __init__(self, content, tags=None, related_entities=None, timestamp=None):
            """
            Initialize a new memory.
            
            Args:
                content (str): The memory content text
                tags (list): List of tags categorizing the memory
                related_entities (list): Names of entities related to this memory
                timestamp (datetime): When the memory was created
            """
            self.content = content
            self.tags = tags or []
            self.related_entities = related_entities or []
            self.timestamp = timestamp or datetime.now()
            self.access_count = 0  # Track how often this memory is accessed
            self._hash = hash(self.content)  # Create a hash for comparison
        
        def to_dict(self):
            """Convert memory to dictionary for serialization"""
            return {
                "content": self.content,
                "tags": self.tags,
                "related_entities": self.related_entities,
                "timestamp": str(self.timestamp),
                "access_count": self.access_count
            }
        
        @classmethod
        def from_dict(cls, data):
            """Create memory from dictionary"""
            memory = cls(
                content=data["content"],
                tags=data["tags"],
                related_entities=data["related_entities"]
            )
            memory.access_count = data.get("access_count", 0)
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
            
        # These methods allow Python to compare Memory objects
        def __lt__(self, other):
            """Less than comparison based on timestamp"""
            if not isinstance(other, Memory):
                return NotImplemented
            return self.timestamp < other.timestamp
            
        def __le__(self, other):
            """Less than or equal comparison based on timestamp"""
            if not isinstance(other, Memory):
                return NotImplemented
            return self.timestamp <= other.timestamp
            
        def __gt__(self, other):
            """Greater than comparison based on timestamp"""
            if not isinstance(other, Memory):
                return NotImplemented
            return self.timestamp > other.timestamp
            
        def __ge__(self, other):
            """Greater than or equal comparison based on timestamp"""
            if not isinstance(other, Memory):
                return NotImplemented
            return self.timestamp >= other.timestamp


    class MemorySystem:
        """
        Manages the storage, retrieval, and maintenance of game memories.
        """
        def __init__(self):
            self.memories = []
            self.entity_index = defaultdict(list)  # For quick lookup by entity
            self.tag_index = defaultdict(list)     # For quick lookup by tag
        
        def add_memory(self, content, tags=None, related_entities=None):
            """
            Add a new memory to the system.
            
            Args:
                content (str): The memory content
                tags (list): Tags for categorization (e.g., "Critical", "Character", "Location")
                related_entities (list): Entities mentioned in the memory
                
            Returns:
                Memory: The created memory object
            """
            # Create the memory
            memory = Memory(content, tags, related_entities)
            
            # Add to main list
            self.memories.append(memory)
            
            # Update indexes for fast retrieval
            for entity in memory.related_entities:
                self.entity_index[entity.lower()].append(memory)
                
            for tag in memory.tags:
                self.tag_index[tag.lower()].append(memory)
                
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
            return sorted(self.memories, key=lambda m: m.timestamp, reverse=True)[:count]
        
        def build_context(self, current_location=None, present_npcs=None, active_quests=None, max_tokens=1000):
            """
            Build a relevant context from memories for the current game state.
            
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
            
            # Take top elements based on token budget (rough approximation)
            selected_memories = []
            total_length = 0
            for _, memory in scored_memories:
                # Rough token estimation (~4 chars per token)
                memory_length = len(memory.content)
                if total_length + memory_length > max_tokens * 4:
                    break
                selected_memories.append(memory)
                total_length += memory_length
            
            # Format the context
            formatted_context = self._format_context(selected_memories)
            return formatted_context
        
        def _score_memory_relevance(self, memory, current_location, present_npcs, active_quests):
            """Score a memory's relevance to the current game state"""
            score = 0
            
            # Critical memories always get high score
            if "Critical" in memory.tags:
                score += 10
            
            # Recent memories are more relevant
            if memory in self.get_recent_memories(5):
                score += 5
            elif memory in self.get_recent_memories(10):
                score += 3
                
            # Location relevance
            if current_location and current_location.lower() in [e.lower() for e in memory.related_entities]:
                score += 4
                
            # NPC relevance
            if present_npcs:
                for npc in present_npcs:
                    if npc.lower() in [e.lower() for e in memory.related_entities]:
                        score += 3
            
            # Quest relevance
            if active_quests:
                for quest in active_quests:
                    if quest.lower() in [e.lower() for e in memory.related_entities]:
                        score += 5
            
            # Tag importance
            tag_scores = {
                "major": 3,
                "plot": 4,
                "character": 2,
                "location": 2,
                "minor": -1
            }
            
            for tag in memory.tags:
                tag_lower = tag.lower()
                if tag_lower in tag_scores:
                    score += tag_scores[tag_lower]
            
            # Access count - memories that have been recalled often are important
            score += min(memory.access_count, 5) * 0.5
            
            return score
        
        def _format_context(self, memories):
            """Format a list of memories into a coherent context string"""
            if not memories:
                return "No relevant memories."
            
            # Group memories by type
            character_memories = [m for m in memories if "Character" in m.tags]
            plot_memories = [m for m in memories if "Plot" in m.tags]
            location_memories = [m for m in memories if "Location" in m.tags]
            other_memories = [m for m in memories if not any(t in m.tags for t in ["Character", "Plot", "Location"])]
            
            formatted = []
            
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
            
            if other_memories:
                formatted.append("Other memories:")
                for memory in other_memories:
                    formatted.append(f"- {memory.content}")
            
            return "\n".join(formatted)
        
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
                        if entity.lower() in sentence.lower():
                            related_entities.append(entity)
                
                # Basic heuristics for tagging
                # These are simplified - you would expand this based on your game's needs
                if any(word in sentence.lower() for word in ["discover", "found", "revealed", "secret", "hidden"]):
                    tags.append("Discovery")
                    
                if any(word in sentence.lower() for word in ["quest", "mission", "task", "objective"]):
                    tags.append("Quest")
                    
                if re.search(r'(?i)you (gain|earned|learned|acquired|received|got|have)', sentence):
                    tags.append("Acquisition")
                    
                if any(word in sentence.lower() for word in ["critical", "important", "essential", "key", "vital"]):
                    tags.append("Critical")
                
                # Only add if we have some tags or entities
                if tags or related_entities:
                    potential_memories.append({
                        "content": sentence,
                        "tags": tags,
                        "related_entities": related_entities
                    })
            
            return potential_memories
            
        # Replace persistent storage with save-file specific storage
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
                    
                    for memory in self.memories:
                        for entity in memory.related_entities:
                            self.entity_index[entity.lower()].append(memory)
                        for tag in memory.tags:
                            self.tag_index[tag.lower()].append(memory)
                except Exception as e:
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
        
