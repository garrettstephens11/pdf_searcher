from flask import Flask, render_template, request, jsonify
import PyPDF2
import pdfminer
from pdfminer.high_level import extract_text
import io
import re

app = Flask(__name__)

def search_pdf(pdf_data, search_term):
    search_results = []

    with io.BytesIO(pdf_data) as file:
        # Extract text from PDF
        text = extract_text(file)
        # Split text into paragraphs
        paragraphs = text.split('\n\n')

        for p_index, paragraph in enumerate(paragraphs):
            # Find sentences containing search_term
            sentences = re.findall(r'[^.!?]*[.!?]', paragraph)
            for sentence in sentences:
                if search_term.lower() in sentence.lower():
                    search_results.append({
                        'sentence': sentence.strip(),
                        'paragraph': paragraph.strip(),
                        'page_number': None
                    })

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
    app.run(debug=True)
