import pandas as pd
import numpy as np
from gensim.models.word2vec import Word2Vec
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from gensim.models.phrases import Phraser
import re
from stop_words import get_stop_words
from nltk import pos_tag

# Word score and stem mapping
stem_df = pd.read_csv('stem_map.csv')

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

        Returns list of tuples with:

        - list of word expansions from the recommended stem
        - list of parts of speech of the word expansions
        - gender category of the stem
        - similarity score """

    recommendations = []
    if gender is None and pos is None:
        sim_tuples = model.most_similar(get_stem_from_word(word), topn=topn)
        for sim_tuple in sim_tuples:
            stem_results = stem_df[stem_df.stem == sim_tuple[0]]
            recommendations.append((stem_results.word.tolist(),
                                    stem_results.pos.tolist(),
                                    stem_results.category.tolist()[0],
                                    round(sim_tuple[1], 3)))
        return recommendations
    else:
        sim_tuples = model.most_similar(get_stem_from_word(word), topn=1000)
        if pos is None:
            if isinstance(gender, str):
                gender = [gender]
            ok_words = stem_df.stem[stem_df.category.isin(gender)].tolist()
        elif gender is None:
            pos = pos.upper()
            ok_words = stem_df.stem[stem_df.pos.str.contains(pos)].tolist()
        else:
            if isinstance(gender, str):
                gender = [gender]
            pos = pos.upper()
            ok_words = stem_df.stem[(stem_df.category.isin(gender)) & (stem_df.pos.str.contains(pos))].tolist()
        count = 0
        for sim_tuple in sim_tuples:
            if sim_tuple[0] in ok_words:
                stem_results = stem_df[stem_df.stem == sim_tuple[0]]
                recommendations.append((stem_results.word.tolist(),
                                        stem_results.pos.tolist(),
                                        stem_results.category.tolist()[0],
                                        round(sim_tuple[1], 3)))
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

    results = []
    for token_tuple in processed_text:
        cat = stem_df.category[stem_df.stem == token_tuple[0]].get_values()
        if len(cat) > 0 and cat[0] != 'Neutral' and cat[0] is not np.nan:
            results.append((token_tuple[0], token_tuple[1], token_tuple[2], cat[0]))
    return results


def highlight_gendered_words(text, gendered_word_results):
    """ Highlight gendered words from gendered_word_results and raw text

        Returns string """

    for result in gendered_word_results:
        highlight_regex = re.compile(r'\b({})\b'.format(' '.join(result[1].split('_'))), re.IGNORECASE)
        text = re.sub(highlight_regex, r'<em>\1</em>', text)
    return text
