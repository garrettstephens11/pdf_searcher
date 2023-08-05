from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import openai
import fitz  # PyMuPDF
import re
from nltk.tokenize import word_tokenize, sent_tokenize
import os  # Import the os module

app = Flask(__name__)

# Get your secret key from an environment variable
app.secret_key = os.getenv('SECRET_KEY')

# Set OpenAI settings from environment variables
openai.organization = os.getenv('OPENAI_ORG_ID')
openai.api_key = os.getenv('OPENAI_API_KEY')

def clean_text(text):
    # Replace multiple whitespaces, newlines, and tabs with a single space
    cleaned_text = re.sub(r'\s+', ' ', text)
    return cleaned_text

def extract_pdf_text(pdf_data):
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # Split the text into sentences
    sentences = sent_tokenize(text)

    # Group every 5 sentences into a paragraph
    paragraphs = [' '.join(sentences[i:i+5]) for i in range(0, len(sentences), 5)]

    # Join the paragraphs with two newlines between each
    text = '\n\n'.join(paragraphs)

    # Remove extra spaces before periods
    text = text.replace(' .', '.')

    return clean_text(text)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_data = request.files['pdf_file'].read()

        text = extract_pdf_text(pdf_data)
        tokens = word_tokenize(text)
        segments = [' '.join(tokens[i:i+2000]) for i in range(0, len(tokens), 2000)]  # Reduced to 2000 words

        # Enumerate the segments before passing to the template
        enumerated_segments = list(enumerate(segments))

        return render_template('result.html', segments=enumerated_segments, discussions=session.get('discussions'))

    # Clear the 'discussions' session data when the route is accessed with a GET request
    session.pop('discussions', None)

    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    index = request.form.get('index')
    segment = request.form.get('segment')
    print(f'Generating for index: {index}, segment: {segment[:100]}...')  # Print the first 100 characters of the segment for brevity

    # Construct the prompt
    prompt = "Can you generate for me a short book club discussion between three people about the following section of a book: {}. This discussion should address the book club question: 'What is a random word or phrase that for some reason stood out to you in reading this text? What does that word or phrase bring to mind for you? Then, relate your own thought back to the passage's message.'".format(segment)

    # Generate the discussion
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    discussion = response.choices[0].message['content']

    # Store the discussion in the session so it can be accessed in the index route
    if 'discussions' not in session:
        session['discussions'] = {}
    session['discussions'][str(index)] = discussion
    print(f'Sessions after generation:  {session["discussions"]}')

    # Return the discussion as a JSON response
    return jsonify(discussion=discussion)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
