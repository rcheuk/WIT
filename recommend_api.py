import json
from flask import Flask, request

from recommend_words import get_most_similar, read_text, process_text, get_gendered_words, highlight_gendered_words

app = Flask(__name__)

@app.route('/')
def hello():
	return 'Hello World'

@app.route('/recommend')
def recommend():
    try:
        word = request.args.get('word')
        topn = request.args.get('topn', default=10, type=int)
        gender = request.args.get('gender', default=None)
        pos = request.args.get('pos', default=None)

        if gender is not None:
            gender = gender.split(',')

        if pos is not None:
            pos = pos.split(',')

        recommendations = get_most_similar(word, topn=topn, gender=gender, pos=pos)
        return json.dumps({'recommendations': recommendations}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({'error': str(e)}, ensure_ascii=False)

@app.route('/analyze_document')
def analyze_document():
    try:
        file = request.args.get('file')
        text = read_text(file)
        processed_text = process_text(text)
        word_data = get_gendered_words(processed_text)
        highlighted_text = highlight_gendered_words(text, word_data)
        return json.dumps({'highlighted_text': str(highlighted_text)}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({'error': str(e)}, ensure_ascii=False)

if __name__ == "__main__":
	app.run(host='127.0.0.1', port=8000)