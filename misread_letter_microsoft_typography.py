import streamlit as st
import pandas as pd
import re
import unicodedata
import Levenshtein

# Constants 
DATA_FILE_URL = "https://github.com/mythicsociety/KannadaTools/raw/94814a2766fd22e89e24976eded769d45a82560a/mythic_society%20(1).xlsx"
INSCRIPTION_1_COLOR = "#FF0000"
INSCRIPTION_2_COLOR = "#0000FF"
KANNADA_CHAR_RANGE = r'[\u0C80-\u0CFF]'
SPECIAL_CHARS_REGEX = r'[^\w\s\u0C80-\u0CFF\u200c|]'

# Load data (with caching) 
@st.cache_data(ttl=3600)
def load_inscription_data():
    """Loads inscription data from the Excel file."""
    return pd.read_excel(DATA_FILE_URL)

# Tokenize Kannada text 
# Tokenize Kannada text 
def tokenize_kannada(text, preserve_whitespace=False):  
    """
    Splits Kannada text into tokens based on syllable patterns.
    This function splits Kannada text into logical linguistic units (aksharas).
    
    Args:
        text: The input Kannada text to be tokenized.
        preserve_whitespace: A flag to indicate whether to preserve spaces in the output tokens. (Ignored in this version)
    
    Returns:
        List of tokens (aksharas) from the text.
    """

    # Define character classes based on Unicode categories for Kannada
    consonants = r'[\u0C95-\u0CB9\u0CDE]'  # Kannada consonants
    vowels = r'[\u0C85-\u0C94]'  # Kannada vowels
    halant = r'\u0CCD'  # Halant (Virama)
    nukta = r'[\u0C82-\u0C83]'  # Anusvara, Visarga
    vowel_signs = r'[\u0CBE-\u0CCD]'  # Vowel modifiers, dependent vowel signs
    zwj = r'\u200D'  # Zero Width Joiner
    zwnj = r'\u200C'  # Zero Width Non-Joiner
    non_kannada = r'[^\u0C80-\u0CFF\s]'  # Any non-Kannada characters

    # The pattern for a syllable: consonant cluster + vowel or standalone vowel
    syllable_pattern = f"""
        ({consonants}{halant}?{zwj}?)?  # Optional consonant with halant and optional ZWJ
        {vowels}?                       # Optional standalone vowel
        ({consonants}{halant})?          # Optional consonant followed by halant
        ({vowel_signs})*                 # Optional vowel signs (diacritics)
        ({nukta})*                       # Optional nukta (Anusvara/Visarga)
    """

    # Clean the text of any non-Kannada characters
    text = clean_inscription_text(text)

    # Compile the pattern and find matches
    combined_pattern = re.compile(syllable_pattern, re.VERBOSE | re.UNICODE)
    matches = combined_pattern.finditer(text)

    # Extract tokens
    tokens = [match.group(0) for match in matches]

    # Always strip leading/trailing spaces in tokens
    tokens = [token.strip() for token in tokens if token.strip()]

    return tokens



# Create misread dictionary (with caching) 
@st.cache_resource
def get_misread_dict(dataframe):
    """Creates a dictionary of misread aksharas and their corrections."""
    misread_dict = {}
    for _, row in dataframe.iterrows():
        misread_akshara = row['different_aksharas_in_sentence1']
        corrected_akshara = row['different_aksharas_in_sentence2']

        if pd.notna(misread_akshara) and pd.notna(corrected_akshara):
            if misread_akshara not in misread_dict:
                misread_dict[misread_akshara] = [corrected_akshara]
            else:
                if corrected_akshara not in misread_dict[misread_akshara]:
                    misread_dict[misread_akshara].append(corrected_akshara)

    return misread_dict

# Predict potential misreads 
def predict_misreads(sentence, misread_dict):
    """Predicts potential misread aksharas in a sentence."""
    potential_misreads = {}
    tokens = tokenize_kannada(sentence)  

    for token in tokens:
        if token in misread_dict:
            potential_misreads[token] = misread_dict[token]

    return potential_misreads

# Clean text 
def clean_inscription_text(text):
    """Cleans inscription text by removing special characters and extra whitespace."""
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = ' '.join(text.split())
    text = re.sub(SPECIAL_CHARS_REGEX, '', text)
    return text

# Count aksharas 
def count_aksharas(text):
    """Counts the number of aksharas in Kannada text."""
    text = clean_inscription_text(text)
    words = re.split(r'(\s+|\|)', text)
    tokens = []
    for word in words:
        if word.strip() and word != '|':
            tokens.extend(tokenize_kannada(word))  
        elif word == '|':
            tokens.append(word)
    tokens = [token for token in tokens if token.strip()]
    return len(tokens)

# Get Levenshtein differences 
def get_levenshtein_diffs(seq1, seq2):
    """Compares two sequences and returns Levenshtein differences."""
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

# Compare lines with highlighting 
def compare_and_highlight_lines(text1, text2, color1, color2):
    """
    Compares two Kannada texts line by line, highlighting differences.
    """
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    max_len = max(len(lines1), len(lines2))
    results = []
    total_differences = 0
    comparison_results = []

    for i in range(max_len):
        line1 = lines1[i] if i < len(lines1) else ""
        line2 = lines2[i] if i < len(lines2) else ""
        cleaned_line1 = clean_inscription_text(line1)
        cleaned_line2 = clean_inscription_text(line2)

        inscription_1_tokens = tokenize_kannada(cleaned_line1, preserve_whitespace=True) 
        inscription_2_tokens = tokenize_kannada(cleaned_line2, preserve_whitespace=True) 

        differences_seq = get_levenshtein_diffs(inscription_1_tokens, inscription_2_tokens)

        # Filter out empty tuples from differences_seq
        differences_seq = [diff for diff in differences_seq if diff != ('', '')]

        if not differences_seq:
            results.append((cleaned_line1, cleaned_line2, "This line is the same in both inscriptions", 0))
            highlighted_line2 = f"<span style='color:{color1}'>{cleaned_line2}</span>"
            comparison_results.append((line1, line2, cleaned_line1, highlighted_line2, "", 0))
        else:
            edit_ops = Levenshtein.editops(inscription_1_tokens, inscription_2_tokens)
            highlighted_line2 = ""
            i, j = 0, 0
            line_differences = 0

            for op, i1, i2 in edit_ops:
                while j < i2:
                    highlighted_line2 += f"<span style='color:{color1}'>{inscription_2_tokens[j]}</span>"
                    j += 1

                if op == 'replace':
                    replace_length = len(tokenize_kannada(inscription_1_tokens[i1])) 
                    highlighted_line2 += f"<span style='color:{color2}'>{''.join(inscription_2_tokens[i2:i2 + replace_length])}</span>"
                    i, j = i1 + 1, i2 + replace_length
                    line_differences += replace_length
                elif op == 'delete':
                    i = i1 + 1
                    line_differences += 1
                elif op == 'insert':
                    highlighted_line2 += f"<span style='color:{color2}'>{inscription_2_tokens[i2]}</span>"
                    j = i2 + 1
                    line_differences += 1

            while j < len(inscription_2_tokens):
                highlighted_line2 += f"<span style='color:{color1}'>{inscription_2_tokens[j]}</span>"
                j += 1

            formatted_differences = '; '.join([
                f"""(<span style='color:{color1}'>{'&nbsp;' if not diff[0] else ''.join(diff[0])}</span>, <span style='color:{color2}'>{'&nbsp;' if not diff[1] else ''.join(diff[1])}</span>)"""
                for diff in differences_seq
            ])

            total_differences += line_differences

            results.append((cleaned_line1, highlighted_line2, formatted_differences, line_differences))
            comparison_results.append((line1, line2, cleaned_line1, highlighted_line2, formatted_differences, line_differences))

    return comparison_results, total_differences  

# Process text for akshara count 
def count_aksharas_per_line(text):
    """
    Processes Kannada text, counting aksharas per line and the total.

    Args:
        text: The Kannada text to process.

    Returns:
        A tuple containing:
        - line_akshara_counts: a list of akshara counts for each line.
        - total_aksharas: the total number of aksharas in the text.
        - num_lines: the number of lines in the text.
    """
    lines = text.splitlines()
    total_aksharas = 0
    line_akshara_counts = []
    for line in lines:
        if line.strip():
            cleaned_line = clean_inscription_text(line)
            # Split the cleaned line into words, treating whitespace and the pipe symbol '|' as delimiters. 
            # The pipe symbol is likely used to mark specific separations or boundaries within the inscription text
            words = re.split(r'(\s+|\|)', cleaned_line)
            word_tokens = []
            for word in words:
                if word.strip() and word != '|':
                    word_tokens.extend(tokenize_kannada(word))  
                elif word == '|':
                    word_tokens.append(word)
            akshara_count = len([token for token in word_tokens if token.strip()])
            line_akshara_counts.append(akshara_count)
            total_aksharas += akshara_count
    return line_akshara_counts, total_aksharas, len(lines)

# Load the DataFrame
df = load_inscription_data()

# Create misread dictionary 
misread_dict = get_misread_dict(df)

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
with st.expander(""): 
    sentence = st.text_input("Enter Kannada sentences from an inscription to predict potential misread aksharas and corrections")
    if sentence: 
        if not re.search(KANNADA_CHAR_RANGE, sentence): 
            st.warning("Please enter only Kannada text") 
        else:
            result = predict_misreads(sentence, misread_dict) 
            if result: 
                st.write("Observations made during the correction of over 200 inscriptions from the Bengaluru region suggest that the following aksharas in the provided inscription may have been misread:")
                for miss_read, corrections in result.items(): 
                    st.write(f"'{miss_read}' could be misread as {', '.join(corrections)}") 
            else:
                st.write("No possible misreads found.") 

# Aksharas Counter section
st.markdown("<div class='custom-header'>Aksharas Counter</div>", unsafe_allow_html=True)
with st.expander(""):  
    text = st.text_area("Enter the Kannada inscription text to count the number of aksharas in:", "")
    st.markdown("<span class='note-line' style='color:blue'>Note: Any special characters such as *,),},],?,., etc in the inscription text will not be counted</span>", unsafe_allow_html=True)  
    if st.button("Process Text"):  
        if not text.strip():  
            st.warning("Please enter some Kannada text")  
        elif not re.search(KANNADA_CHAR_RANGE, text):  
            st.warning("Please enter text in Kannada script only")  
        else:
            try:
                line_akshara_counts, total_aksharas, num_lines = count_aksharas_per_line(text) 

                st.markdown(f"This inscription contains <span style='color:red'>{total_aksharas} aksharas</span> in <span style='color:blue'>{num_lines} lines</span>.", unsafe_allow_html=True) 

                st.write("---")

                for i, akshara_count in enumerate(line_akshara_counts):
                    st.markdown(f"<span style='color:red'>Line {i+1}</span> contains <span style='color:blue'>{akshara_count}</span> aksharas.", unsafe_allow_html=True) 

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# Compare The Text of Two Kannada Inscriptions section
st.markdown("<div class='custom-header'>Compare The Text of Two Kannada Inscriptions</div>", unsafe_allow_html=True)
with st.expander(""):
    col1, col2 = st.columns(2)

    with col1:
        inscription_1_text = st.text_area("Enter Kannada text of inscription 1 in the text box below:", "")
        color1 = st.color_picker("Select color for Inscription 1:", INSCRIPTION_1_COLOR)

    with col2:
        inscription_2_text = st.text_area("Enter Kannada text of inscription 2 in the text box below:", "")
        color2 = st.color_picker("Select color for Inscription 2:", INSCRIPTION_2_COLOR)

    st.markdown("<span class='note_line' style='color:blue'>Note: 1) Any special characters such as *,),},],?,., etc in the inscription text will not be counted or compared.</span>", unsafe_allow_html=True)
    st.markdown("<span class='note_line' style='color:blue'>      2) The coloured differences indicated below for inscription 2 lines may sometimes be wrong. Please recheck the 'as input' and 'as processed lines' to understand why that may be</span>", unsafe_allow_html=True)

    if st.button("Compare Inscriptions"):
        if not inscription_1_text.strip() or not inscription_2_text.strip():
            st.warning("Please enter Kannada text in both text boxes")
        elif not re.search(KANNADA_CHAR_RANGE, inscription_1_text) or not re.search(KANNADA_CHAR_RANGE, inscription_2_text):
            st.warning("Please enter text in Kannada script only in both text boxes")
        else:
            try:
                if inscription_1_text:
                    line_akshara_counts1, total_aksharas1, num_lines1 = count_aksharas_per_line(inscription_1_text) 
                    lines1 = inscription_1_text.splitlines() 
                else:
                    total_aksharas1 = 0
                    num_lines1 = 0
                    lines1 = []

                if inscription_2_text:
                    line_akshara_counts2, total_aksharas2, num_lines2 = count_aksharas_per_line(inscription_2_text) 
                    lines2 = inscription_2_text.splitlines()
                else:
                    total_aksharas2 = 0
                    num_lines2 = 0
                    lines2 = []

                st.write(f"Inscription 1 contains {total_aksharas1} aksharas in {num_lines1} lines")
                st.write(f"Inscription 2 contains {total_aksharas2} aksharas in {num_lines2} lines")

                with st.spinner("Comparing inscriptions..."):
                    comparison_results, total_differences = compare_and_highlight_lines(inscription_1_text, inscription_2_text, color1, color2)

                # Display original and cleaned lines along with the side-by-side comparison
                max_len = max(len(lines1), len(lines2))
                for i in range(max_len):
                    line1 = lines1[i] if i < len(lines1) else ""
                    line2 = lines2[i] if i < len(lines2) else ""
                    cleaned_line1 = clean_inscription_text(line1)
                    cleaned_line2 = clean_inscription_text(line2)

                    # Get highlighted_line2 from comparison_results
                    _, _, _, highlighted_line2, differences, line_differences = comparison_results[i]

                    # Rearrange columns: Original 1, Original 2, Cleaned 1, Highlighted 2
                    col1, col3, col2, col4 = st.columns(4)

                    with col1:
                        st.write(f"**Line {i + 1}**")
                        st.write(f"As input in inscription 1: {line1}") 

                    with col3:
                        st.write(f"**Line {i + 1}**")
                        st.write(f"As input in inscription 2: {line2}") 

                    with col2:
                        st.write(f"**Line {i + 1}**")
                        st.write(f"As processed for inscription 1: <span style='color:{color1}'>{cleaned_line1}</span>", unsafe_allow_html=True)

                    with col4:
                        st.write(f"**Line {i + 1}**")
                        st.markdown(f"<p>As processed for inscription 2: {highlighted_line2}</p>", unsafe_allow_html=True) 
                        if line_differences > 0:
                            st.write(f"Akshara differences: {line_differences}")
                            st.markdown(differences, unsafe_allow_html=True)

                    st.write("---")

                if total_aksharas1 > 0:
                    difference_rate = total_differences / total_aksharas1
                    st.write(f"**Total akshara differences:** {total_differences}")
                    st.write(f"**Difference rate:** {difference_rate:.2%}")
                else:
                    st.write("Cannot calculate difference rate as inscription 1 has no aksharas.")

            except Exception as e:
                st.error(f"An error occurred during inscription comparison: {e}")

st.markdown("""
<hr style="height:2px;border-width:0;color:gray;background-color:gray">
""", unsafe_allow_html=True)

# Attribution
st.markdown("<div style='text-align: center;'>The first version of these software utilities were developed by Ujwala Yadav and Deepthi B J during their internship with the Mythic Society Bengaluru Inscriptions 3D Digital Conservation Project</div>", unsafe_allow_html=True)