import streamlit as st
import pandas as pd
import re
import unicodedata
import Levenshtein

# Define the URL to your Excel file hosted on GitHub (raw format)
# FILE_URL = "https://github.com/mythicsociety/KannadaTools/raw/5dd7b887899184df5965a19d6ddc5914bd6d37ce/mythic_society.xlsx"
# FILE_URL = "https://github.com/saatvikpaul19/myt/raw/0aed2a4cdd23a0028264c8984359c85879131e77/mythic_society%20(1).xlsx"
FILE_URL = "https://github.com/mythicsociety/KannadaTools/raw/94814a2766fd22e89e24976eded769d45a82560a/mythic_society%20(1).xlsx"

# Load the data from the Excel file
df = pd.read_excel(FILE_URL)


# Function to split Kannada text into tokens
def split_kannada_text(text):
    tokens = []
    i = 0
    while i < len(text):
        char = text[i]
        token = char
        i += 1

        while i < len(text) and (unicodedata.category(text[i]) in ('Mn', 'Mc', 'Me') or (text[i] == '್' and i+1 < len(text) and unicodedata.category(text[i+1]) == 'Lo')):
            if text[i] == '\u200c':
                break
            token += text[i]
            i += 1
            if text[i-1] == '್' and i < len(text) and unicodedata.category(text[i]) == 'Lo':
                token += text[i]
                i += 1

        token = token.replace('\u200c', '')
        tokens.append(token)

    return tokens

# Function to create the miss_read_dict from the DataFrame
def create_miss_read_dict(df):
    miss_read_dict = {}
    for index, row in df.iterrows():
        miss_read_akshara = row['different_aksharas_in_sentence1']
        corrected_letter = row['different_aksharas_in_sentence2']

        if pd.notna(miss_read_akshara) and pd.notna(corrected_letter):
            if miss_read_akshara not in miss_read_dict:
                miss_read_dict[miss_read_akshara] = [corrected_letter]
            else:
                if corrected_letter not in miss_read_dict[miss_read_akshara]:
                    miss_read_dict[miss_read_akshara].append(corrected_letter)

    return miss_read_dict

# Function to predict possible miss-reads in a sentence
def predict_miss_read(sentence, miss_read_dict):
    possible_misreads = {}
    tokens = split_kannada_text(sentence)

    for token in tokens:
        if token in miss_read_dict:
            possible_misreads[token] = miss_read_dict[token]

    return possible_misreads

# Function to clean text
def clean_text(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = ' '.join(text.split())
    text = re.sub(r'[^\w\s\u0C80-\u0CFF\u200c|]', '', text)
    return text


def split_kannada_text_diff(text):
    tokens = []
    i = 0
    while i < len(text):
        char = text[i]
        token = char
        i += 1

        if char.isspace():
            continue

        while (i < len(text) and
               (unicodedata.category(text[i]) in ('Mn', 'Mc', 'Me') or
                (text[i] == '್' and i+1 < len(text) and unicodedata.category(text[i+1]) == 'Lo'))):
            token += text[i]
            i += 1
            if text[i-1] == '್' and i < len(text) and unicodedata.category(text[i]) == 'Lo':
                token += text[i]
                i += 1

        tokens.append(token)

    return tokens

def count_words(text):
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

def compare_lines(text1, text2):
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    max_len = max(len(lines1), len(lines2))
    results = []
    total_differences = 0  # Initialize total_differences here

    for i in range(max_len):
        line1 = lines1[i] if i < len(lines1) else ""
        line2 = lines2[i] if i < len(lines2) else ""
        line1 = clean_text(line1)
        line2 = clean_text(line2)
        seq1_tokens = split_kannada_text_diff(line1)
        seq2_tokens = split_kannada_text_diff(line2)

        differences_seq = get_differences2(seq1_tokens, seq2_tokens)

        formatted_differences = '; '.join([
            f"""(<span style='color:red'>{'&nbsp;' if not diff[0] else ''.join(diff[0])}</span>, <span style='color:blue'>{'&nbsp;' if not diff[1] else ''.join(diff[1])}</span>)"""
            for diff in differences_seq
        ])

        # Calculate akshara differences for this line
        line_differences = 0
        for diff in differences_seq:
            if diff[1]:  # Check if there's a change in the second inscription
                line_differences += len(split_kannada_text(diff[1]))  # Count aksharas in the changed part

        total_differences += line_differences  # Add to the overall count

        results.append((line1, line2, formatted_differences, line_differences))  # Include line_differences in results

    return results, total_differences  # Return total_differences along with results


def process_text(text):
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
    return line_word_counts, total_words, len(lines)  # Return line_word_counts instead of total_words

# Create the miss_read_dict from the DataFrame
miss_read_dict = create_miss_read_dict(df)

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

st.markdown("<span class='note-line' style='color:blue'>*Note: While this program has only been tested for Kannada, it may work for other Indic scripts as well*</span>", unsafe_allow_html=True)

# Potential Misread Akshara Predictor section
st.markdown("<div class='custom-header'>Potential Misread Akshara Predictor</div>", unsafe_allow_html=True) 
with st.expander(""):
    sentence = st.text_input("Enter Kannada sentences from an inscription to predict potential misread aksharas and corrections")
    if sentence:
        result = predict_miss_read(sentence, miss_read_dict)
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
        try:
            line_word_counts, total_words, num_lines = process_text(text)

            st.markdown(f"<span style='color:red'>Total number of aksharas: {total_words}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:blue'>Total number of sentences: {num_lines}</span>", unsafe_allow_html=True)
            st.write("---")

            for i, word_count in enumerate(line_word_counts):
                st.write(f"Number of aksharas in sentence {i+1} is {word_count}")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

# Compare The Text of Two Kannada Inscriptions section
st.markdown("<div class='custom-header'>Compare The Text of Two Kannada Inscriptions</div>", unsafe_allow_html=True)
with st.expander(""):
    col1, col2 = st.columns(2)

    with col1:
        seq1 = st.text_area("Enter text of inscription 1:", "")
        if seq1:
            line_word_counts1, total_aksharas1, num_lines1 = process_text(seq1)
            st.write(f"Inscription 1 contains {total_aksharas1} aksharas in {num_lines1} lines")

    with col2:
        seq2 = st.text_area("Enter text of inscription 2:", "")
        if seq2:
            line_word_counts2, total_aksharas2, num_lines2 = process_text(seq2)  # Assign num_lines2 here
            st.write(f"Inscription 2 contains  {total_aksharas2} aksharas in {num_lines2} lines") 

    st.markdown("<span class='note-line' style='color:blue'>Note: Any special characters such as *,),},],?,., etc in the inscription text will not be counted or compared.</span>", unsafe_allow_html=True)
    if st.button("Compare Inscriptions"):
        comparison_results, total_differences = compare_lines(seq1, seq2)

        for i, (line1, line2, differences, line_differences) in enumerate(comparison_results):
            if differences:
                st.write(f"Differences in inscription texts in line {i+1}: ({line_differences} aksharas)")
                
                # Print the entire lines with specified colors
                st.markdown(f"<span style='color:red'>{line1}</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:blue'>{line2}</span>", unsafe_allow_html=True)

                st.markdown(differences, unsafe_allow_html=True)

            st.write("---")

        # Calculate and display the difference rate
        if total_aksharas1 > 0:  # Avoid division by zero
            difference_rate = total_differences / total_aksharas1
            st.write(f"{total_differences} aksharas are different between inscription 2 and inscription 1. Therefore, the difference rate is {difference_rate:.2%}")
        #   st.write(f"The difference rate is {difference_rate:.2%}") 
        else:
            st.write("Cannot calculate difference rate as Inscription 1 has no aksharas.")
        # Add the full-width double separator line with custom CSS
        st.markdown("""
        <hr style="height:2px;border-width:0;color:gray;background-color:gray">
        """, unsafe_allow_html=True)

# Attribution at the bottom
st.markdown("<div style='text-align: center;'>The first version of these software utilities were developed by Ujwala Yadav and Deepthi B J during their internship with the Mythic Society Bengaluru Inscriptions 3D Digital Conservation Project</div>", unsafe_allow_html=True)