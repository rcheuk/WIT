import json
import urllib
from flask import Flask, request, make_response, current_app
from datetime import timedelta
from functools import update_wrapper

from recommend_words import get_most_similar, process_text, get_gendered_words, highlight_gendered_words

app = Flask(__name__)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.route('/', methods=['GET', 'POST'])
@crossdomain(origin='*')
def hello():
    return 'Hello World!'


@app.route('/recommend', methods=['GET', 'POST'])
@crossdomain(origin='*')
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


@app.route('/analyze_document', methods=['GET', 'POST'])
@crossdomain(origin='*')
def analyze_document():
    try:
        data = json.loads(urllib.parse.unquote(request.data))
        text = data['text']
        processed_text = process_text(text)
        word_data = get_gendered_words(processed_text)
        highlighted_text = highlight_gendered_words(text, word_data)
        return json.dumps({'highlighted_text': str(highlighted_text)}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({'error': str(e)}, ensure_ascii=False)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000)
