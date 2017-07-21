from flask import Flask, render_template, request, url_for, Markup
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectField

from recommend_words import get_most_similar, process_text, get_gendered_words, highlight_gendered_words

class DocumentForm(FlaskForm):
  text = TextAreaField("Enter document text to analyze:")
  submitdoc = SubmitField("Analyze")

class WordForm(FlaskForm):
  word = StringField("Enter a word or two word phrase to get recommendations:")
  strongly_male = BooleanField("Strongly Male")
  male = BooleanField("Male")
  neutral = BooleanField("Neutral")
  female = BooleanField("Female")
  strongly_female = BooleanField("Strongly Female")
  pos = SelectField('Part of Speech', choices=[('any', 'Any'), ('NOUN', 'Noun'), ('VERB', 'Verb'),
                                                      ('ADJ', 'Adjective'), ('ADV', 'Adverb')])
  submitword = SubmitField("Recommend")

app = Flask(__name__)
app.secret_key = 'development key'

@app.route('/')
def forms():
    document_form = DocumentForm()
    word_form = WordForm()
    return render_template('form_submit.html', document_form=document_form, word_form=word_form)

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        word = request.form['word'].replace(' ', '_')
        gender = [g for g in ['strongly_male', 'male', 'neutral', 'female', 'strongly_female'] if g in request.form]
        if len(gender) == 0 or len(gender) == 5:
            gender = None
        pos = request.form['pos']
        if pos == 'any':
            pos = None
        topn = 10

        recommendations = get_most_similar(word, topn=topn, gender=gender, pos=pos)
        return render_template('word_recommendations.html', recommendations=recommendations)

    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/analyze_document', methods=['POST'])
def analyze_document():
    try:
        text = request.form['text']
        processed_text = process_text(text)
        word_data = get_gendered_words(processed_text)
        highlighted_text = highlight_gendered_words(text, word_data)
        return render_template('analyzed_document.html', highlighted_text=Markup(highlighted_text))

    except Exception as e:
        return render_template('error.html', error=str(e))

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000)
