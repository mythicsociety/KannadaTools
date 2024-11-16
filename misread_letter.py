import streamlit as st
import pandas as pd
import re
from tools.kannadaTools import clean_inscription_text, compare_and_highlight_lines, count_aksharas_per_line, predict_misreads, load_inscription_data, get_misread_dict

# Constants 
INSCRIPTION_1_COLOR = "#FF0000"
INSCRIPTION_2_COLOR = "#0000FF"
KANNADA_CHAR_RANGE = r'[\u0C80-\u0CFF]'
SPECIAL_CHARS_REGEX = r'[^\w\s\u0C80-\u0CFF\u200c|]'

# Define the GitHub repository URL
repo_url = "https://github.com/mythicsociety/KannadaTools"  

# Define the URL you want to link to
levenshtein_url = "https://en.wikipedia.org/wiki/Levenshtein_distance"  

# Load data (with caching) 
@st.cache_data(ttl=3600)
def load_data():
    """Loads inscription data from the Excel file."""
    return load_inscription_data()

# Create misread dictionary (with caching) 
@st.cache_resource
def get_dict(dataframe):
    """Creates a dictionary of misread aksharas and their corrections."""
    return get_misread_dict(dataframe)

# Load the DataFrame
df = load_data()

# Create misread dictionary 
misread_dict = get_dict(df)

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

    st.markdown(f"""
    <span class='note_line' style='color:blue'>      2) This program utilizes the <a href="{levenshtein_url}" target="_blank">Levenshtein algorithm</a> to compare two Kannada inscriptions. While this algorithm is primarily designed for alphabets, it has been adapted in this instance to function with the Kannada syllabary. It's important to note that in rare cases, the highlighted differences in inscription 2 might be inaccurate. If you observe any discrepancies, please double-check the 'as input' and 'as processed' lines for further verification.</span>
    """, unsafe_allow_html=True)

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

                    # Rearrange columns: Line Number, Original 1, Original 2, Cleaned 1, Highlighted 2
                    col0, col1, col3, col2, col4 = st.columns(5)  # Added col0 for line number

                    with col0:
                        st.write(f"**{i + 1}**")  # Display line number only once

                    with col1:
                        st.write(f"As input in inscription 1: {line1}") 

                    with col3:
                        st.write(f"As input in inscription 2: {line2}") 

                    with col2:
                        st.write(f"As processed for inscription 1: <span style='color:{color1}'>{cleaned_line1}</span>", unsafe_allow_html=True)

                    with col4:
                        st.markdown(f"<p>As processed for inscription 2: {highlighted_line2}</p>", unsafe_allow_html=True) 
                        if line_differences > 0:
                            st.write(f"Akshara differences: {line_differences}")
                            st.markdown(differences, unsafe_allow_html=True)
                        else:  # Add this condition
                            st.markdown("<span style='color:green'>This line is the same in both inscriptions</span>", unsafe_allow_html=True)

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
st.markdown("<div style='text-align: center;'>The first version of these software utilities were developed by Ujwala Yadav and Deepthi B J during their internship with the Mythic Society Bengaluru Inscriptions 3D Digital Conservation Project. API added by Karthik Aditya</div>", unsafe_allow_html=True)

# Separate line for project and code link
st.markdown(f"""
<div style='text-align: center;'>
For more about this project, please visit the <a href="{repo_url}" target="_blank">GitHub Repository</a>
</div>
""", unsafe_allow_html=True)
# Feedback Line
st.markdown("<div style='text-align: center;'>For feedback about these utilities please write to <a href='mailto:3dscanning.mythicsociety@gmail.com'>3dscanning.mythicsociety@gmail.com</a></div>", unsafe_allow_html=True)