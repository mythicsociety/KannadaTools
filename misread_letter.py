import streamlit as st
import pandas as pd
import re
import unicodedata
import Levenshtein

# Define constants for file URLs and other frequently used values
FILE_URL = "https://github.com/mythicsociety/KannadaTools/raw/94814a2766fd22e89e24976eded769d45a82560a/mythic_society%20(1).xlsx"
INSCRIPTION_1_COLOR = "#FF0000"  # Default color for Inscription 1
INSCRIPTION_2_COLOR = "#0000FF"  # Default color for Inscription 2
KANNADA_CHAR_RANGE = r'[\u0C80-\u0CFF]'  # Regular expression for Kannada characters
SPECIAL_CHARS_REGEX = r'[^\w\s\u0C80-\u0CFF\u200c|]'  # Regular expression for special characters

# Load the data from the Excel file using caching
@st.cache_data(ttl=3600)  # Cache for 1 hour (adjust as needed)
def load_data():
    """Loads data from the Excel file at FILE_URL."""
    return pd.read_excel(FILE_URL)

df = load_data()

# Function to split Kannada text into tokens
def split_kannada_text(text, preserve_spaces=False):
    """
    Splits Kannada text into tokens, optionally preserving whitespace.

    Args:
        text: The Kannada text to be split.
        preserve_spaces: If True, whitespace characters are treated as separate tokens.

    Returns:
        A list of Kannada tokens.
    """
    tokens = []  # Initialize an empty list to store the tokens
    char_index = 0  # Initialize a variable to keep track of the current character index
    while char_index < len(text):  # Iterate through each character in the text
        char = text[char_index]  # Get the current character
        token = char  # Initialize a token with the current character
        char_index += 1  # Move to the next character

        if not preserve_spaces and char.isspace():
            continue  # Skip whitespace if not preserving

        # Handle combining characters and vowel signs
        while char_index < len(text) and (
            unicodedata.category(text[char_index]) in ('Mn', 'Mc', 'Me') 
            or (text[char_index] == '್' and char_index + 1 < len(text) and unicodedata.category(text[char_index + 1]) == 'Lo')
        ):
            token += text[char_index]  # Add the combining character or vowel sign to the token
            char_index += 1
            if text[char_index - 1] == '್' and char_index < len(text) and unicodedata.category(text[char_index]) == 'Lo':
                token += text[char_index]  # Add the dependent vowel to the token
                char_index += 1

        token = token.replace('\u200c', '')  # Remove zero-width non-joiner
        tokens.append(token)  # Add the completed token to the list

    return tokens  # Return the list of tokens


# Function to create the miss_read_dict from the DataFrame, also caching
@st.cache_resource 
def create_miss_read_dict_cached(df):
    """
    Creates a dictionary of misread aksharas and their corrections from the DataFrame.

    Args:
        df: The pandas DataFrame containing the misread and corrected aksharas.

    Returns:
        A dictionary where keys are misread aksharas and values are lists of possible corrections.
    """
    miss_read_dict = {}  # Initialize an empty dictionary to store the misread aksharas and their corrections
    for _, row in df.iterrows():  # Iterate through each row of the DataFrame
        miss_read_akshara = row['different_aksharas_in_sentence1']  # Extract the misread akshara from the first sentence
        corrected_letter = row['different_aksharas_in_sentence2']  # Extract the corrected akshara from the second sentence

        # Check if both misread and corrected aksharas are valid (not NaN)
        if pd.notna(miss_read_akshara) and pd.notna(corrected_letter):
            if miss_read_akshara not in miss_read_dict:  # If the misread akshara is not already in the dictionary
                miss_read_dict[miss_read_akshara] = [corrected_letter]  # Create a new entry with the corrected letter as the first element in the list
            else:
                if corrected_letter not in miss_read_dict[miss_read_akshara]:  # If the corrected letter is not already in the list of corrections for this misread akshara
                    miss_read_dict[miss_read_akshara].append(corrected_letter)  # Add the corrected letter to the list of corrections

    return miss_read_dict  # Return the dictionary of misread aksharas and their corrections


# Function to predict possible miss-reads in a sentence
def predict_miss_read(sentence, miss_read_dict):
    """
    Predicts possible misread aksharas in a sentence based on the miss_read_dict.

    Args:
        sentence: The Kannada sentence to analyze.
        miss_read_dict: A dictionary of misread aksharas and their corrections.

    Returns:
        A dictionary where keys are potentially misread aksharas and values are lists of possible corrections.
    """
    possible_misreads = {}  # Initialize an empty dictionary to store the possible misreads
    tokens = split_kannada_text(sentence)  # Split the sentence into tokens

    for token in tokens:  # Iterate through each token in the sentence
        if token in miss_read_dict:  # If the token is found in the miss_read_dict
            possible_misreads[token] = miss_read_dict[token]  # Add the token and its possible corrections to the possible_misreads dictionary

    return possible_misreads  # Return the dictionary of possible misreads


# Function to clean text
def clean_text(text):
    """
    Cleans the input text by removing special characters and extra whitespace.

    Args:
        text: The text to be cleaned.

    Returns:
        The cleaned text.
    """
    text = re.sub(r'\[.*?\]', '', text)  # Remove text within square brackets
    text = re.sub(r'\(.*?\)', '', text)  # Remove text within parentheses
    text = ' '.join(text.split())  # Normalize whitespace
    text = re.sub(SPECIAL_CHARS_REGEX, '', text)  # Remove special characters
    return text


def split_kannada_text_diff(text):
    """
    Splits Kannada text into tokens, preserving whitespace

    Args:
        text: the Kannada text to split

    Returns:
        a list of Kannada tokens, including whitespace as separate tokens
    """
    return split_kannada_text(text, preserve_spaces=True)


def count_words(text):
    """
    Counts the number of words (aksharas) in the given Kannada text.

    Args:
        text: The Kannada text to be processed

    Returns:
        The total number of words (aksharas) in the text
    """
    text = clean_text(text)
    words = re.split(r'(\s+|\|)', text)
    tokens = []
    for word in words:
        if word.strip() and word != '|':
            tokens.extend(split_kannada_text(word))
        elif word == '|':
            tokens.append(word)
    tokens = [token for token in tokens if token.strip()]
    total_word_count = len(tokens)
    return total_word_count

def get_differences2(seq1, seq2):
    """
    Compares two sequences and returns the differences between them using Levenshtein distance.

    Args:
        seq1: The first sequence to compare
        seq2: The second sequence to compare

    Returns:
        A list of tuples representing the differences between the sequences. Each tuple contains
        the corresponding elements from seq1 and seq2 that are different
    """
    edit_ops = Levenshtein.editops(seq1, seq2)
    differences = []
    for op, i1, i2 in edit_ops:
        if op == 'replace':
            differences.append((seq1[i1], seq2[i2]))
        elif op == 'delete':
            differences.append((seq1[i1], ''))
        elif op == 'insert':
            differences.append(('', seq2[i2]))
    return differences

def get_differences2(seq1, seq2):
    """
    Compares two sequences and returns the differences between them using Levenshtein distance.

    Args:
        seq1: The first sequence to compare
        seq2: The second sequence to compare

    Returns:
        A list of tuples representing the differences between the sequences. Each tuple contains
        the corresponding elements from seq1 and seq2 that are different
    """
    edit_ops = Levenshtein.editops(seq1, seq2)  # Get the edit operations required to transform seq1 into seq2
    differences = []  # Initialize an empty list to store the differences
    for op, i1, i2 in edit_ops:  # Iterate through each edit operation
        if op == 'replace':  # If the operation is a replacement
            differences.append((seq1[i1], seq2[i2]))  # Add the differing elements from both sequences
        elif op == 'delete':  # If the operation is a deletion
            differences.append((seq1[i1], ''))  # Add the deleted element from seq1 and an empty string for seq2
        elif op == 'insert':  # If the operation is an insertion
            differences.append(('', seq2[i2]))  # Add an empty string for seq1 and the inserted element from seq2
    return differences  # Return the list of differences


def compare_lines(text1, text2, color1, color2):
    """
    Compares two Kannada texts line by line, highlighting differences and providing a summary

    Args:
        text1: The first Kannada text to compare
        text2: The second Kannada text to compare
        color1: The color to use for highlighting elements in text1
        color2: The color to use for highlighting elements in text2

    Returns:
        A tuple containing
        - results: A list of tuples, each representing a line comparison with
                   (original line1, highlighted line2, formatted differences, number of differences in the line)
        - total differences: The total number of aksharas that differ between the two texts
    """
    lines1 = text1.splitlines()  # Split the first text into lines
    lines2 = text2.splitlines()  # Split the second text into lines
    max_len = max(len(lines1), len(lines2))  # Get the maximum number of lines between the two texts
    results = []  # Initialize an empty list to store the comparison results for each line
    total_differences = 0  # Initialize a variable to keep track of the total number of differences

    for i in range(max_len):  # Iterate through each line (up to the maximum number of lines)
        line1 = lines1[i] if i < len(lines1) else ""  # Get the current line or an empty string if it doesn't exist
        line2 = lines2[i] if i < len(lines2) else ""
        line1 = clean_text(line1)  # Clean both lines
        line2 = clean_text(line2)
        seq1_tokens = split_kannada_text_diff(line1)  # Split into tokens, preserving spaces
        seq2_tokens = split_kannada_text_diff(line2)

        differences_seq = get_differences2(seq1_tokens, seq2_tokens)  # Get the differences between the token sequences

        # Highlight differing aksharas in line2 in color2, the rest in color1
        highlighted_line2 = ""
        j = 0  # Index to track position in seq2_tokens
        for diff in differences_seq:
            if diff[0]:  # If there's a difference in seq1 (not an insertion in seq2)
                while j < len(seq2_tokens) and seq2_tokens[j] != diff[1]:
                    highlighted_line2 += f"<span style='color:{color1}'>{seq2_tokens[j]}</span>"  # Highlight matching parts in color1
                    j += 1
                if j < len(seq2_tokens) and seq2_tokens[j] == diff[1]:
                    highlighted_line2 += f"<span style='color:{color2}'>{seq2_tokens[j]}</span>"  # Highlight the difference in color2
                    j += 1
            else:  # This is an insertion in seq2
                highlighted_line2 += f"<span style='color:{color2}'>{diff[1]}</span>"  # Highlight the insertion in color2

        # Highlight any remaining matching parts in color1
        highlighted_line2 += "".join([f"<span style='color:{color1}'>{token}</span>" for token in seq2_tokens[j:]])

        # Format the differences for display
        formatted_differences = '; '.join([
            f"""(<span style='color:{color1}'>{'&nbsp;' if not diff[0] else ''.join(diff[0])}</span>, <span style='color:{color2}'>{'&nbsp;' if not diff[1] else ''.join(diff[1])}</span>)"""
            for diff in differences_seq
        ])

        line_differences = 0 
        for diff in differences_seq:
            if diff[1]:  # Count the number of differing aksharas in this line
                line_differences += len(split_kannada_text(diff[1]))

        total_differences += line_differences  # Accumulate the total differences

        results.append((line1, highlighted_line2, formatted_differences, line_differences))  # Store the comparison results for this line

    return results, total_differences


def process_text(text):
    """
    Processes the given Kannada text, counting aksharas per line and the total.

    Args:
        text: The Kannada text to process

    Returns:
        A tuple containing:
        - line_word_counts: a list of akshara counts for each line
        - total_words: the total number of aksharas in the text
        - num_lines: the number of lines in the text
    """
    lines = text.splitlines()
    total_words = 0
    line_word_counts = []
    for line in lines:
        if line.strip():
            cleaned_line = clean_text(line)
            words = re.split(r'(\s+|\|)', cleaned_line)
            word_tokens = []
            for word in words:
                if word.strip() and word != '|':
                    word_tokens.extend(split_kannada_text(word))
                elif word == '|':
                    word_tokens.append(word)
            word_count = len([token for token in word_tokens if token.strip()])
            line_word_counts.append(word_count)
            total_words += word_count
    return line_word_counts, total_words, len(lines)


# Create the miss_read_dict from the DataFrame
miss_read_dict = create_miss_read_dict_cached(df)

# Streamlit UI
st.markdown("""
<style>
.title-container {
    text-align: center; 
}

.title-line1 {
    font-size: 38px !important; 
    font-weight: bold;
}

.title-line2 {
    font-size: 24px !important; 
}

.note-line {
    text-align: center;
}

/* Style for custom section headers */
.custom-header {
    font-size: 24px !important; 
    font-weight: bold;
    margin-bottom: 10px; 
}
</style>

<div class="title-container">
<span class="title-line1">Software Utilities for Working With Kannada Inscriptions</span>
<br>
<span class="title-line2">These software utilities are used extensively by the Mythic Society Bengaluru Inscriptions 3D Digital Conservation Project Team. They were developed because off-the-shelf software is unable to perform these tasks correctly.</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<span class='note-line' style='color:blue'>*Note: This program has been designed and tested for only Kannada, it will not work for other Indic scripts*</span>", unsafe_allow_html=True)

# Potential Misread Akshara Predictor section
st.markdown("<div class='custom-header'>Potential Misread Akshara Predictor</div>", unsafe_allow_html=True)
with st.expander(""):  # Create an expandable section for the predictor
    sentence = st.text_input("Enter Kannada sentences from an inscription to predict potential misread aksharas and corrections")  # Get user input for Kannada sentences
    if sentence:  # If the user has entered some text
        # Input validation: Check for Kannada characters
        if not re.search(KANNADA_CHAR_RANGE, sentence):  # Check if the input contains Kannada characters
            st.warning("Please enter only Kannada text")  # Display a warning if no Kannada characters are found
        else:
            result = predict_miss_read(sentence, miss_read_dict)  # Predict potential misreads using the provided sentence and the miss_read_dict
            if result:  # If there are potential misreads
                st.write("Observations made during the correction of over 200 inscriptions from the Bengaluru region suggest that the following aksharas in the provided inscription may have been misread:")  # Display a message about the potential misreads
                for miss_read, corrections in result.items():  # Iterate through the misreads and their corrections
                    st.write(f"'{miss_read}' could be misread as {', '.join(corrections)}")  # Display each misread and its possible corrections
            else:
                st.write("No possible misreads found.")  # Display a message if no misreads are found

# Aksharas Counter section
st.markdown("<div class='custom-header'>Aksharas Counter</div>", unsafe_allow_html=True)
with st.expander(""):  # Create an expandable section for the aksharas counter
    text = st.text_area("Enter the Kannada inscription text to count the number of aksharas in:", "")  # Get user input for the Kannada inscription text
    st.markdown("<span class='note-line' style='color:blue'>Note: Any special characters such as *,),},],?,., etc in the inscription text will not be counted</span>", unsafe_allow_html=True)  # Display a note about special characters
    if st.button("Process Text"):  # If the "Process Text" button is clicked
        if not text.strip():  # If the input text is empty
            st.warning("Please enter some Kannada text")  # Display a warning
        # Input validation: Check for Kannada characters
        elif not re.search(KANNADA_CHAR_RANGE, text):  # Check if the input contains Kannada characters
            st.warning("Please enter text in Kannada script only")  # Display a warning if no Kannada characters are found
        else:
            try:
                line_word_counts, total_words, num_lines = process_text(text)  # Process the text to get akshara counts and number of lines

                st.markdown(f"<span style='color:red'>Total number of aksharas: {total_words}</span>", unsafe_allow_html=True)  # Display the total number of aksharas
                st.markdown(f"<span style='color:blue'>Total number of sentences: {num_lines}</span>", unsafe_allow_html=True)  # Display the total number of sentences
                st.write("---")  # Add a separator

                for i, word_count in enumerate(line_word_counts):  # Iterate through the akshara counts for each line
                    st.write(f"Number of aksharas in sentence {i+1} is {word_count}")  # Display the akshara count for each sentence

            except Exception as e:  # Handle any unexpected errors
                st.error(f"An unexpected error occurred: {e}")  # Display an error message

# Compare The Text of Two Kannada Inscriptions section
st.markdown("<div class='custom-header'>Compare The Text of Two Kannada Inscriptions</div>", unsafe_allow_html=True)  # Add a custom header for this section
with st.expander(""):  # Create an expandable section for inscription comparison
    col1, col2 = st.columns(2)  # Create two columns for side-by-side layout

    with col1:  # First column for inscription 1
        seq1 = st.text_area("Enter Kannada text of inscription 1 in the text box below:", "")  # Get user input for the first inscription

        # Add color picker for Inscription 1 beneath its text area
        color1 = st.color_picker("Select color for Inscription 1:", INSCRIPTION_1_COLOR) 

    with col2:  # Second column for inscription 2
        seq2 = st.text_area("Enter Kannada text of inscription 2 in the text box below:", "")  # Get user input for the second inscription

        # Add color picker for Inscription 2 beneath its text area
        color2 = st.color_picker("Select color for Inscription 2:", INSCRIPTION_2_COLOR) 

    
    st.markdown("<span class='note-line' style='color:blue'>Note: 1) Any special characters such as *,),},],?,., etc in the inscription text will not be counted or compared.</span>", unsafe_allow_html=True)  # Display a note about special characters
    st.markdown("<span class='note-line' style='color:blue'>      2) The coloured differences indicated below for inscription 2 lines may be wrong when the line contains a '0'. Please recheck the output for all lines containing 0s</span>", unsafe_allow_html=True)  # Display a note about special characters
    if st.button("Compare Inscriptions"):  # If the "Compare Inscriptions" button is clicked
        if not seq1.strip() or not seq2.strip():  # If either inscription text is empty
            st.warning("Please enter Kannada text in both text boxes")  # Display a warning
        # Input validation: Check for Kannada characters BEFORE processing
        elif not re.search(KANNADA_CHAR_RANGE, seq1) or not re.search(KANNADA_CHAR_RANGE, seq2):  # Check if both inputs contain Kannada characters
            st.warning("Please enter text in Kannada script only in both text boxes")  # Display a warning if no Kannada characters are found
        else:
            # Now process the text to get akshara counts and number of lines
            if seq1: 
                line_word_counts1, total_aksharas1, num_lines1 = process_text(seq1) 
                st.write(f"Inscription 1 contains {total_aksharas1} aksharas in {num_lines1} lines")

            if seq2: 
                line_word_counts2, total_aksharas2, num_lines2 = process_text(seq2)
                st.write(f"Inscription 2 contains  {total_aksharas2} aksharas in {num_lines2} lines")

            with st.spinner("Comparing inscriptions..."):  # Display a spinner while comparing
                comparison_results, total_differences = compare_lines(seq1, seq2, color1, color2)  # Compare the inscriptions and get the results

            for i, (line1, highlighted_line2, differences, line_differences) in enumerate(comparison_results):  # Iterate through the comparison results for each line
                  
                    st.write(f" {line_differences} aksharas differ in line {i+1} between inscription 2 and inscription 1")  # Display the number of differing aksharas in the line

                    st.markdown(f"<span style='color:{color1}'>{line1}</span>", unsafe_allow_html=True)  # Display the original line from inscription 1
                    st.markdown(highlighted_line2, unsafe_allow_html=True)  # Display the highlighted line from inscription 2 with differences marked

                    st.markdown(differences, unsafe_allow_html=True)  # Display the formatted differences

                    st.write("---")  # Add a separator

            if total_aksharas1 > 0:  # If inscription 1 has aksharas
                difference_rate = total_differences / total_aksharas1  # Calculate the difference rate
                st.write(f"{total_differences} aksharas are different between inscription 2 and inscription 1. Therefore, the difference rate is {difference_rate:.2%}")  # Display the total differences and the difference rate
            else:
                st.write("Cannot calculate difference rate as inscription 1 has no aksharas.")  # Display a message if inscription 1 is empty

            st.markdown("""
            <hr style="height:2px;border-width:0;color:gray;background-color:gray">
            """, unsafe_allow_html=True)  # Add a horizontal line separator

# Attribution at the bottom
st.markdown("<div style='text-align: center;'>The first version of these software utilities were developed by Ujwala Yadav and Deepthi B J during their internship with the Mythic Society Bengaluru Inscriptions 3D Digital Conservation Project</div>", unsafe_allow_html=True)  # Display attribution information