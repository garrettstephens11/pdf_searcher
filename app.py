from flask import Flask, render_template, request, jsonify
import io
import regex as re
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=5)

def clean_text(text):
    # Replace multiple whitespaces, newlines, and tabs with a single space
    cleaned_text = re.sub(r'\s+', ' ', text)

    # Split the text into sentences
    sentences = cleaned_text.split('. ')

    # Capitalize the first letter of each sentence and capitalize 'i'
    cleaned_sentences = [sentence[0].upper() + sentence[1:].replace(' i ', ' I ') if len(sentence) > 0 else '' for sentence in sentences]

    # Join the sentences back together
    cleaned_text = '. '.join(cleaned_sentences)

    return cleaned_text

def search_page(args):
    page_number, page, search_term = args
    search_results = []
    text = page.get_text()

    paragraphs = text.split('\n\n')

    for p_index, paragraph in enumerate(paragraphs):
        sentences = re.findall(r'[^.!?]*[.!?]', paragraph)
        for sentence in sentences:
            if search_term.lower() in sentence.lower():
                search_results.append({
                    'sentence': clean_text(sentence.strip()),
                    'paragraph': clean_text(paragraph.strip()),
                    'page_number': page_number
                })
    return search_results

def search_pdf(pdf_data, search_term):
    search_results = []
    search_term_lower = search_term.lower()

    doc = fitz.open(stream=pdf_data, filetype="pdf")
    
    page_data = [(i, page, search_term) for i, page in enumerate(doc)]
    
    results = executor.map(search_page, page_data)
    for page_result in results:
        if page_result:
            search_results.extend(page_result)

    return search_results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_term = request.form['search_term']
        pdf_data = request.files['pdf_file'].read()

        search_results = search_pdf(pdf_data, search_term)

        return jsonify(search_results)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
