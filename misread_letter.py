import streamlit as st
import pandas as pd
import re
import unicodedata
import Levenshtein

# Define the path to your Excel file
FILE_PATH = "C:\\WorkingFiles\\NMKRVCharAnalysis\\30aug24\\mythic_society (1).xlsx"  
# Load the data from the Excel file
df = pd.read_excel(FILE_PATH)

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
    if not text.strip():
        raise EmptyInputError("The input text is empty.")
    text = clean_text(text)
    if not text:
        raise InvalidInputError("The input text does not contain valid Kannada characters after cleaning.")
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
    for i in range(max_len):
        line1 = lines1[i] if i < len(lines1) else ""
        line2 = lines2[i] if i < len(lines2) else ""
        line1 = clean_text(line1)
        line2 = clean_text(line2)
        seq1_tokens = split_kannada_text_diff(line1)
        seq2_tokens = split_kannada_text_diff(line2)
        differences_seq = get_differences2(seq1_tokens, seq2_tokens)
        results.append((line1, line2, differences_seq))
    return results

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
    return line_word_counts, total_words, len(lines)

# Create the miss_read_dict from the DataFrame
miss_read_dict = create_miss_read_dict(df)

# Streamlit UI
st.title("Compare Kannada Sentences, Count Aksharas and Predict Potential Misread Aksharas")

st.header("Potential Misread Akshara Predictor")
sentence = st.text_input("Enter a Kannada sentence to check for possible misreads")
if sentence:
    result = predict_miss_read(sentence, miss_read_dict)
    if result:
        st.write("Possible misreads and corrections:")
        for miss_read, corrections in result.items():
            st.write(f"'{miss_read}' could be misread as {', '.join(corrections)}")
    else:
        st.write("No possible misreads found.")

st.header("Akshara Counter")
text = st.text_area("Enter the Kannada text:", "")
if st.button("Process Text"):
    try:
        line_word_counts, total_words, num_lines = process_text(text)
        for i, word_count in enumerate(line_word_counts):
            st.write(f"Sentence {i+1}:")
            st.write(f"Akshara count: {word_count}")
            st.write("---")
        st.write(f"Total number of aksharas: {total_words}")
        st.write(f"Total number of sentences: {num_lines}")
    except EmptyInputError as e:
        st.error(f"Error: {e}")
    except InvalidInputError as e:
        st.error(f"Error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

st.header("Compare Two Kannada Sentences")
seq1 = st.text_area("Enter sentence 1:", "")
seq2 = st.text_area("Enter sentence 2:", "")
if st.button("Compare Sentences"):
    comparison_results = compare_lines(seq1, seq2)
    for i, (line1, line2, differences) in enumerate(comparison_results):
        st.write(f"Line {i+1}:")
        st.write(f"Sentence 1: {line1}")
        st.write(f"Sentence 2: {line2}")
        st.write("Differences:")
        for diff in differences:
            st.write(f"({''.join(diff[0])}, {''.join(diff[1])})")
        st.write("---")

