# Function: load_inscription_data (with caching)
    IF data is in cache:
        Retrieve data from cache
    ELSE:
        Load Excel data from the provided URL
        Store the loaded data in cache
    RETURN the loaded data

# Function: tokenize_kannada
    Initialize an empty list to store tokens
    Start at the beginning of the text
    WHILE there are more characters to process:
        Get the current character
        Start a new token with this character
        Move to the next character

        IF preserve_whitespace is FALSE AND the character is a space:
            Skip to the next character

        WHILE there are more characters AND the next character is a combining mark OR a vowel modifier followed by a vowel:
            Add the next character to the current token
            Move to the next character
            IF the previous character was a vowel modifier AND the current character is a vowel:
                Add the current character to the token
                Move to the next character

        Remove any zero-width non-joiner characters from the token
        Add the token to the list of tokens

    RETURN the list of tokens

# Function: create_misread_dictionary (with caching)
    IF the misread dictionary is already cached:
        Retrieve it from the cache
    ELSE:
        Create an empty dictionary to store misread aksharas and their corrections
        FOR each row in the provided dataframe:
            Get the misread akshara and its corrected version from the row
            IF both the misread and corrected aksharas are valid:
                IF the misread akshara is not already in the dictionary:
                    Add it to the dictionary with its correction as the value (in a list)
                ELSE IF the corrected akshara is not already in the list of corrections for this misread akshara:
                    Add the corrected akshara to the list of corrections
        Store the created dictionary in the cache
    RETURN the misread dictionary

# Function: predict_potential_misreads
    Create an empty dictionary to store potential misreads and their corrections
    Tokenize the input sentence
    FOR each token in the tokenized sentence:
        IF the token is found in the misread dictionary:
            Add the token and its corresponding corrections from the dictionary to the potential misreads dictionary
    RETURN the potential misreads dictionary

# Function: clean_inscription_text
    Remove any text enclosed in square brackets or parentheses
    Normalize whitespace by replacing multiple spaces with a single space
    Remove any special characters that are not Kannada letters, numbers, whitespace, or the pipe symbol
    RETURN the cleaned text

# Function: count_aksharas
    Clean the input text
    Split the cleaned text into words using whitespace and the pipe symbol as delimiters
    Create an empty list to store tokens
    FOR each word in the list of words:
        IF the word is not empty and is not the pipe symbol:
            Tokenize the word and add the tokens to the list
        ELSE IF the word is the pipe symbol:
            Add the pipe symbol to the list of tokens
    Filter out any empty tokens from the list
    RETURN the number of tokens in the list

# Function: get_levenshtein_differences
    Calculate the edit operations required to transform the first sequence into the second sequence
    Create an empty list to store the differences
    FOR each edit operation:
        IF the operation is a replacement:
            Add a tuple containing the original and replaced characters to the list of differences
        ELSE IF the operation is a deletion:
            Add a tuple containing the deleted character and an empty string to the list of differences
        ELSE IF the operation is an insertion
            Add a tuple containing an empty string and the inserted character to the list of differences
    RETURN the list of differences

# Function: compare_lines_with_highlighting
    Split the first and second texts into lines
    Find the maximum number of lines between the two texts
    Create empty lists to store the results and comparison results
    Initialize a variable to keep track of the total number of differences
    FOR each line index up to the maximum number of lines
        Get the corresponding lines from the first and second texts, or empty strings if the index is out of bounds
        Clean both lines
        Tokenize both cleaned lines, preserving whitespace
        Find the differences between the tokenized lines using the Levenshtein distance
        IF there are no differences:
            Add a result indicating no differences and 0 differences
            Highlight the second cleaned line with the first color
            Add a comparison result with the original lines, cleaned lines, highlighted second line, an empty differences string, and 0 differences
        ELSE
            Calculate the edit operations required to transform the first tokenized line into the second tokenized line
            Initialize an empty string to store the highlighted second line and counters for iterating through the tokenized lines
            Initialize a variable to keep track of the number of differences in this line
            FOR each edit operation
                Add any unchanged portions of the second tokenized line to the highlighted second line
                Handle replacements, deletions, and insertions, updating the highlighted second line, counters, and the number of differences accordingly
            Add any remaining parts of the second tokenized line to the highlighted second line
            Format the differences into a string
            Add the number of differences in this line to the total number of differences
            Add the results and comparison results for this line
    RETURN the comparison results and the total number of differences

# Function: process_text
    Split the input text into lines
    Initialize a variable to store the total number of aksharas and an empty list to store the number of aksharas per line
    FOR each line in the list of lines
        IF the line is not empty
            Clean the line
            # Split the cleaned line into words, treating whitespace and the pipe symbol '|' as delimiters. The pipe symbol is also used to mark specific separations or boundaries within the inscription text
            Split the cleaned line into words using whitespace and the pipe symbol as delimiters
            Create an empty list to store word tokens
            FOR each word in the list of words
                IF the word is not empty and is not the pipe symbol
                    Tokenize the word and add the tokens to the list of word tokens
                ELSE IF the word is the pipe symbol
                    Add the pipe symbol to the list of word tokens
            Count the number of non-empty tokens in the list of word tokens
            Add this count to the list of aksharas per line
            Add this count to the total number of aksharas
    RETURN the list of aksharas per line, the total number of aksharas, and the number of lines