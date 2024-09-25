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
def tokenize_kannada_text(text, preserve_spaces=False):
    """Splits Kannada text into tokens, optionally preserving whitespace."""
    tokens = []
    char_index = 0
    while char_index < len(text):
        char = text[char_index]
        token = char
        char_index += 1

        if not preserve_spaces and char.isspace():
            continue

        while char_index < len(text) and (
            unicodedata.category(text[char_index]) in ('Mn', 'Mc', 'Me')
            or (text[char_index] == '್' and char_index + 1 < len(text) and unicodedata.category(text[char_index + 1]) == 'Lo')
        ):
            token += text[char_index]
            char_index += 1
            if text[char_index - 1] == '್' and char_index < len(text) and unicodedata.category(text[char_index]) == 'Lo':
                token += text[char_index]
                char_index += 1

        token = token.replace('\u200c', '')
        tokens.append(token)

    return tokens

# Create misread dictionary (with caching)
@st.cache_resource
def create_misread_dictionary(df):
    """Creates a dictionary of misread aksharas and their corrections."""
    misread_dict = {}
    for _, row in df.iterrows():
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
def predict_potential_misreads(sentence, misread_dict):
    """Predicts potential misread aksharas in a sentence."""
    potential_misreads = {}
    tokens = tokenize_kannada_text(sentence)

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

# Tokenize with whitespace preservation
def tokenize_with_whitespace(text):
    """Splits Kannada text into tokens, preserving whitespace."""
    return tokenize_kannada_text(text, preserve_spaces=True)

# Count aksharas
def count_aksharas(text):
    """Counts the number of aksharas in Kannada text."""
    text = clean_inscription_text(text)
    words = re.split(r'(\s+|\|)', text)
    tokens = []
    for word in words:
        if word.strip() and word != '|':
            tokens.extend(tokenize_kannada_text(word))
        elif word == '|':
            tokens.append(word)
    tokens = [token for token in tokens if token.strip()]
    return len(tokens)

# Get Levenshtein differences
def get_levenshtein_differences(seq1, seq2):
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
def compare_lines_with_highlighting(text1, text2, color1, color2):
    """
    Compares two Kannada texts line by line, highlighting differences.

    Args:
        text1: The first Kannada text.
        text2: The second Kannada text.
        color1: Color for text1 highlights.
        color2: Color for text2 highlights.

    Returns:
        A tuple containing:
        - results: List of tuples with (original line1, highlighted line2, formatted differences, difference count).
        - total_differences: Total akshara differences.
    """

    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    max_len = max(len(lines1), len(lines2))
    results = []
    total_differences = 0

    for i in range(max_len):
        line1 = lines1[i] if i < len(lines1) else ""
        line2 = lines2[i] if i < len(lines2) else ""
        line1 = clean_inscription_text(line1)
        line2 = clean_inscription_text(line2)
        seq1_tokens = tokenize_with_whitespace(line1)
        seq2_tokens = tokenize_with_whitespace(line2)

        differences_seq = get_levenshtein_differences(seq1_tokens, seq2_tokens)
        edit_ops = Levenshtein.editops(seq1_tokens, seq2_tokens) 

        if not differences_seq:
            results.append((line1, line2, "This line is the same in both inscriptions", 0))
            continue

        highlighted_line2 = ""
        i, j = 0, 0
        for op, i1, i2 in edit_ops:
            highlighted_line2 += "".join(f"<span style='color:{color1}'>{token}</span>" for token in seq2_tokens[j:i2])

            if op == 'replace':
                highlighted_line2 += f"<span style='color:{color2}'>{seq2_tokens[i2]}</span>"
                i, j = i1 + 1, i2 + 1
            elif op == 'delete':
                i = i1 + 1
            elif op == 'insert':
                highlighted_line2 += f"<span style='color:{color2}'>{seq2_tokens[i2]}</span>"
                j = i2 + 1

        highlighted_line2 += "".join(f"<span style='color:{color1}'>{token}</span>" for token in seq2_tokens[j:])

        formatted_differences = '; '.join([
            f"""(<span style='color:{color1}'>{'&nbsp;' if not diff[0] else ''.join(diff[0])}</span>, <span style='color:{color2}'>{'&nbsp;' if not diff[1] else ''.join(diff[1])}</span>)"""
            for diff in differences_seq
        ])

        line_differences = 0
        for diff in differences_seq:
            if diff[1]:
                line_differences += len(tokenize_kannada_text(diff[1]))

        total_differences += line_differences

        results.append((line1, highlighted_line2, formatted_differences, line_differences))

    return results, total_differences

# Process text for akshara count
def process_text(text):
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
            words = re.split(r'(\s+|\|)', cleaned_line)
            word_tokens = []
            for word in words:
                if word.strip() and word != '|':
                    word_tokens.extend(tokenize_kannada_text(word))
                elif word == '|':
                    word_tokens.append(word)
            akshara_count = len([token for token in word_tokens if token.strip()])
            line_akshara_counts.append(akshara_count)
            total_aksharas += akshara_count
    return line_akshara_counts, total_aksharas, len(lines)

# Load the DataFrame
df = load_inscription_data() # Add this line

# Create misread dictionary
misread_dict = create_misread_dictionary(df)

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
            result = predict_potential_misreads(sentence, misread_dict) 
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
                line_akshara_counts, total_aksharas, num_lines = process_text(text)

                st.markdown(f"This inscription contains <span style='color:red'>{total_aksharas} aksharas</span> in <span style='color:blue'>{num_lines} lines</span>.", unsafe_allow_html=True) 

                st.write("---")

                for i, akshara_count in enumerate(line_akshara_counts):
                    st.markdown(f"<span style='color:red'>Line {i+1}</span> contains <span style='color:blue'>{akshara_count}</span> aksharas.", unsafe_allow_html=True) 

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# Compare The Text of Two Kannada Inscriptions section
# Compare The Text of Two Kannada Inscriptions section
st.markdown("<div class='custom-header'>Compare The Text of Two Kannada Inscriptions</div>", unsafe_allow_html=True)
with st.expander(""): 
    col1, col2 = st.columns(2)  # Create two columns for input

    with col1:
        inscription_1_text = st.text_area("Enter Kannada text of inscription 1 in the text box below:", "")
        color1 = st.color_picker("Select color for Inscription 1:", INSCRIPTION_1_COLOR)

    with col2:
        inscription_2_text = st.text_area("Enter Kannada text of inscription 2 in the text box below:", "")
        color2 = st.color_picker("Select color for Inscription 2:", INSCRIPTION_2_COLOR)

    st.markdown("<span class='note-line' style='color:blue'>Note: 1) Any special characters such as *,),},],?,., etc in the inscription text will not be counted or compared.</span>", unsafe_allow_html=True)
    st.markdown("<span class='note_line' style='color:blue'>      2) The coloured differences indicated below for inscription 2 lines may be wrong when the line contains a '0'. Please recheck the output for all lines containing 0s</span>", unsafe_allow_html=True)

    if st.button("Compare Inscriptions"):
        if not inscription_1_text.strip() or not inscription_2_text.strip():
            st.warning("Please enter Kannada text in both text boxes")
        elif not re.search(KANNADA_CHAR_RANGE, inscription_1_text) or not re.search(KANNADA_CHAR_RANGE, inscription_2_text):
            st.warning("Please enter text in Kannada script only in both text boxes")
        else:
            try:
                if inscription_1_text:
                    line_akshara_counts1, total_aksharas1, num_lines1 = process_text(inscription_1_text)
                else:
                    total_aksharas1 = 0
                    num_lines1 = 0

                if inscription_2_text:
                    line_akshara_counts2, total_aksharas2, num_lines2 = process_text(inscription_2_text)
                else:
                    total_aksharas2 = 0
                    num_lines2 = 0

                st.write(f"Inscription 1 contains {total_aksharas1} aksharas in {num_lines1} lines")
                st.write(f"Inscription 2 contains {total_aksharas2} aksharas in {num_lines2} lines")

                with st.spinner("Comparing inscriptions..."):
                    comparison_results, total_differences = compare_lines_with_highlighting(inscription_1_text, inscription_2_text, color1, color2)

                # Display results side-by-side
                for i, (line1, highlighted_line2, differences, line_differences) in enumerate(comparison_results):
                    col3, col4 = st.columns(2)  # Create two columns for side-by-side display

                    with col3:
                        st.write(f"**Line {i + 1}** (Inscription 1)")
                        st.markdown(f"<span style='color:{color1}'>{line1}</span>", unsafe_allow_html=True)

                    with col4:
                        st.write(f"**Line {i + 1}** (Inscription 2)")
                        st.markdown(highlighted_line2, unsafe_allow_html=True)
                        if line_differences > 0:
                            st.write(f"Akshara differences: {line_differences}")
                            st.markdown(differences, unsafe_allow_html=True)

                    st.write("---")  # Separator between lines

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