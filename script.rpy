# Define game variables
default context = "The game begins in a dark tower. The player is a novice wizard who has just begun their arcane studies."
default player_name = ""
default player_choice = "start the game"

#game image
image bg tower = "images/tower.webp"

# Starting point
label start:
    scene black
    with fade

    "Welcome to Dark Wizard Chronicles."

    $ player_name = renpy.input("What is your name, apprentice?")
    $ context += f" The wizard's name is {player_name}."

    scene bg tower # This would be your tower background image
    with fade

    "Welcome to the Tower of Shadows, [player_name]."
    "Your journey into the arcane arts begins now."

    jump dynamic_story

# Main story loop
label dynamic_story:
    $ story_text, choices = generate_story(context, player_choice)

    "[story_text]"

    menu:
        "[choices[0]]":
            $ player_choice = choices[0]
        "[choices[1]]":
            $ player_choice = choices[1]
        "[choices[2]]":
            $ player_choice = choices[2]

    # Update context with the new story segment and player's choice
    $ context += f"\n\nThe story continued: {story_text}\n\nThe player chose: {player_choice}."

    # Continue the loop
    jump dynamic_story