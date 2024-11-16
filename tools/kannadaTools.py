import pandas as pd
import re
import unicodedata
import Levenshtein

# Constants 
DATA_FILE_URL = "https://github.com/mythicsociety/KannadaTools/raw/94814a2766fd22e89e24976eded769d45a82560a/mythic_society%20(1).xlsx"
KANNADA_CHAR_RANGE = r'[\u0C80-\u0CFF]'
SPECIAL_CHARS_REGEX = r'[^\w\s\u0C80-\u0CFF\u200c|]'

# Global variables 
df = None 
misread_dict = None 

def initialize_globals(): 
    global df 
    global misread_dict 
    # Load the DataFrame 
    df = load_inscription_data() 
    
    # Create misread dictionary
    misread_dict = get_misread_dict(df)

def load_inscription_data():
    """Loads inscription data from the Excel file."""
    return pd.read_excel(DATA_FILE_URL)

# Create misread dictionary (with caching) 
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

# Tokenize Kannada text 
def tokenize_kannada(text, preserve_whitespace=False):
    """Splits Kannada text into tokens, optionally preserving whitespace."""
    tokens = []
    char_index = 0
    while char_index < len(text):
        char = text[char_index]
        token = char
        char_index += 1

        if not preserve_whitespace and char.isspace():
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

df = None
misread_dict = None

# Entry point when the module is executed as a script
if __name__ == "__main__":
    print("This is the starting method of the module.")
    
    # Initialize globals
    initialize_globals()