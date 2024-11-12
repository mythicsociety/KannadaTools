from tools.kannadaTools import load_inscription_data, get_misread_dict, clean_inscription_text, compare_and_highlight_lines, count_aksharas_per_line, predict_misreads, tokenize_kannada

from fastapi import FastAPI
app = FastAPI()

@app.get('/predict_misreads')
def base(sentence: str):
    # Load the DataFrame
    df = load_inscription_data()

    # Create misread dictionary 
    misread_dict = get_misread_dict(df)

    result = predict_misreads(sentence, misread_dict) 
    
    return result

@app.get('/tokenize_kannada')
def base(sentence: str):
    result = tokenize_kannada(sentence) 
    
    return result

@app.get('/count_aksharas_per_line')
def base(sentence: str):
    result = count_aksharas_per_line(sentence) 
    
    return result
