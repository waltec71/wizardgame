init -12 python:
    # Game configuration settings
    
    # Feature Flags
    USE_TEST_MODE = False  # Set to True to use test generators instead of API
    
    # Story Generation Settings
    TEMPERATURE = 0.7  # Controls creativity/randomness (0.0-1.0)
    MAX_TOKENS = 1000  # Maximum length of generated text
    
    # Memory Settings
    MAX_CONTEXT_LENGTH = 8000  # Maximum characters to keep in context