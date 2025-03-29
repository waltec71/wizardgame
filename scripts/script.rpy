# Define game variables
default player_name = ""
default player_choice = "start the game"
default current_location = "Tower of Shadows"
default present_npcs = []
default active_quests = []
default stored_memory_data = None

# Add turn counter
default game_turn = 1

# Track game state
default game_state = {
    "visited_locations": ["Tower of Shadows"],
    "known_npcs": [],
    "inventory": []
}

# Game images
image bg tower = "images/backgrounds/tower.webp"

# Starting point
label start:
    # Load memories if they exist
    $ memory_system.load_from_file()
    
    scene black
    with fade

    "Welcome to Dark Wizard Chronicles."

    $ player_name = renpy.input("What is your name, apprentice?")
    
    # Save player name as a memory
    $ memory_system.add_memory(
        f"Your name is {player_name}, a novice wizard.",
        tags=["Character", "Critical"],
        related_entities=["Player"],
        turn=game_turn
    )
    
    # Save to file
    $ memory_system.save_to_file()

    scene bg tower # Tower background image
    with fade

    "Welcome to the Tower of Shadows, [player_name]."
    "Your journey into the arcane arts begins now."

    jump dynamic_story

# Main story loop
label dynamic_story:
    # Use the EnhancedStoryGenerator for story generation
    $ story_text, choices = EnhancedStoryGenerator.generate_story(
        player_choice,
        current_location=current_location,
        present_npcs=present_npcs,
        active_quests=active_quests
    )
    
    # Split the story text into chunks
    $ story_chunks = chunk_story_text(story_text)
    
    # Display chunks
    call display_story_chunks(story_chunks)
    
    # Dynamic menu generation
    $ choice_selected = renpy.display_menu([(choice, choice) for choice in choices])
    $ player_choice = choice_selected
    
    # Update memory
    $ memory_system.add_memory(
        f"You chose to {player_choice}.",
        tags=["Action", "Recent"],
        related_entities=["Player"],
        turn=game_turn
    )
    $ memory_system.save_to_file()
    
    # Increment turn counter after each choice
    $ game_turn += 1

    # Continue the loop
    jump dynamic_story

# Helper label for displaying story chunks
label display_story_chunks(chunks):
    $ index = 0
    while index < len(chunks):
        "[chunks[index]]"
        $ index += 1
    return

# Memory inspection screen - useful for debugging
screen memory_debug():
    frame:
        xalign 0.5
        yalign 0.5
        xsize 800
        ysize 600
        
        has vbox
        
        label "Memory System Debug"
        
        viewport:
            scrollbars "vertical"
            mousewheel True
            ysize 500
            
            vbox:
                spacing 10
                
                for memory in memory_system.memories:
                    frame:
                        xsize 750
                        
                        vbox:
                            text "[memory.content]"
                            hbox:
                                text "Tags: [', '.join(memory.tags)]" size 14
                                null width 20
                                text "Entities: [', '.join(memory.related_entities)]" size 14