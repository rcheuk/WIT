import numpy as np
from gensim.models.word2vec import Word2Vec
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from gensim.models.phrases import Phraser
import re
from stop_words import get_stop_words
from nltk import pos_tag
from sqlalchemy import create_engine

# Word score and stem mapping
db_connect = create_engine('sqlite:///wit_stem_map.db')

# Word embedding model
model = Word2Vec.load('resumes_word2vec.model')

# Bigrams phraser
bigram = Phraser.load('resumes_bigrams.model')


def get_stem_from_word(word):
    """ Get stem from word """

    p_stemmer = PorterStemmer()
    return '_'.join([p_stemmer.stem(w) for w in word.split('_')])


def get_most_similar(word, topn=10, gender=None, pos=None):
    """ Get most similar words by gender or part of speech

        Returns a list of dictionaries with:

        - 'word': list tuples containing of word expansions from the recommended stem,
           parts of speech, and the gender category of the stem
        - 'similarity': similarity score of recommended stem to input word range [0, 1] """

    conn = db_connect.connect()
    stem = get_stem_from_word(word)
    recommendations = []

    if gender is None and pos is None:
        sim_tuples = model.most_similar(stem, topn=topn)
        for sim_tuple in sim_tuples:
            query = conn.execute('SELECT word, pos, category FROM wit_stem_map WHERE stem = "{}"' \
                                 .format(sim_tuple[0]))
            stem_results = {'word': [i for i in query.cursor.fetchall()],
                            'similarity': round(sim_tuple[1], 3)}
            recommendations.append(stem_results)

        return recommendations
    else:
        sim_tuples = model.most_similar(stem, topn=10000)
        if pos is None:
            if isinstance(gender, str):
                gender = [gender]
            query = conn.execute('SELECT stem FROM wit_stem_map WHERE category IN ("{}")' \
                                 .format('", "'.join(gender)))
            ok_words = [i[0] for i in query.cursor.fetchall()]
        elif gender is None:
            pos = pos.upper()
            query = conn.execute('SELECT stem FROM wit_stem_map WHERE pos LIKE "%{}%"' \
                                 .format(pos))
            ok_words = [i[0] for i in query.cursor.fetchall()]
        else:
            if isinstance(gender, str):
                gender = [gender]
            pos = pos.upper()
            query = conn.execute('SELECT stem FROM wit_stem_map WHERE category IN ("{}") ' \
                                 'AND pos LIKE "%{}%"' \
                                 .format('", "'.join(gender), pos))
            ok_words = [i[0] for i in query.cursor.fetchall()]
        count = 0
        for sim_tuple in sim_tuples:
            if sim_tuple[0] in ok_words:
                query = conn.execute('SELECT word, pos, category FROM wit_stem_map WHERE stem = "{}"' \
                                     .format(sim_tuple[0]))
                stem_results = {'word': [i for i in query.cursor.fetchall()],
                                'similarity': round(sim_tuple[1], 3)}
                recommendations.append(stem_results)
                count += 1
                if count == topn:
                    return recommendations


def read_text(text_file):
    """ Read in text file

        Returns string """

    text = []
    with open(text_file, 'r') as f:
        for line in f:
            text.append(line)
    return ' '.join(text)


def process_text(text):
    """ Process text for analysis

        Returns list of tuples with:

        - stem
        - original word
        - part of speech """

    tokenizer = RegexpTokenizer(r'(?u)\b\w\w{2,}\b')
    en_stop = get_stop_words('en')
    p_stemmer = PorterStemmer()
    text = text.replace('\n', ' ')
    text = text.lower()
    text = text.replace(r'page [0-9]+ of [0-9]+', '')
    text = text.replace(r'((https?:\/\/|www\.|t\.co|ftp:\/\/)[^\s]*)', '')
    text = text.replace(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b', '')
    text = text.strip()
    text = tokenizer.tokenize(text)
    text = [token for token in text if re.match(r'[^0-9]', token)]
    text = bigram[text]
    text = [token for token in text if token not in en_stop]

    # part of speech
    pos = ['_'.join([tag[1] for tag in pos_tag(token.split('_'), tagset='universal')]) for token in text]

    # stems
    stems = ['_'.join([p_stemmer.stem(t) for t in token.split('_')]) for token in text]
    return list(zip(stems, text, pos))


def get_gendered_words(processed_text):
    """ Identify gendered words from processed text

        Returns list of tuples with:

        - stem
        - word
        - part of speech
        - gender category """

    conn = db_connect.connect()
    results = []
    for token_tuple in processed_text:
        query = conn.execute('SELECT category FROM wit_stem_map WHERE stem = "{}"' \
                             .format(token_tuple[0]))
        try:
            category = query.first()[0]
        except Exception as e:
            continue
        if category not in ['Neutral', '']:
            results.append((token_tuple[0], token_tuple[1], token_tuple[2], category))
    return results


def highlight_gendered_words(text, gendered_word_results):
    """ Highlight gendered words from gendered_word_results and raw text

        Returns string """

    for result in gendered_word_results:
        highlight_regex = re.compile(r'\b({})\b'.format(' '.join(result[1].split('_'))), re.IGNORECASE)
        text = re.sub(highlight_regex, r'<em>\1</em>', text)
    return text
