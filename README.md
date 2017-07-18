# Women In Tech Demo

To better target women for tech jobs, we need to write job postings to which women will apply. This means writing job postings in which women can see themselves--job postings that use the language women use to describe themselves.<br>

We use a language model built from thousands of resumes to identify gendered language and make recommendations for replacements. Words are categorized as "Strongly Male", "Male", "Neutral", "Female", and "Strongly Female".<br>

The language model for identifying contextually similar words and bigram parser for pre-processing new text are contained in the files `resumes_word2vec.model` and `resumes_bigrams.model`, respectively. The vocabulary, stem expansions, parts of speech, and gender categories are in the sqlite3 database `wit_stem_map.db`.<br>

The `example.ipynb` notebook demonstrates the core functions:<br>
- `get_most_similar(word, topn=10, gender=None, pos=None)` takes a word, and recommends the n top most contextually similar words, optionally filtered by gender category and/or part of speech. It returns a list of dictionaries, one for each word recommendation, that contain two keys, `'word'` and `'similarity'`. The former is a tuple with the list of word variations contained within the data for the recommended word (e.g., "exceed expectations", "exceeds expectations", "exceeding expectations"), a list with the words' part of speech, and a list of their gender category. The latter is a score of the similarity between the recommended word and the input word on a scale of [0,1].
- `read_text(text_file)` reads in a text file and returns it as a string.
- `process_text(text)` pre-process and tokenizes a text string for use in analysis. It returns a list of tuples for each word token in the text of the form `(word stem, original word, part of speech)`.
- `get_gendered_words(processed_text)` takes the processed_text list and returns a list of tuples for those tokens that are identified as gendered in the form `(word stem, original word, part of speech, gender category)`.
- `highlight_gendered_words(text, gendered_word_list)` take in the raw text and the gendered word list from get_gendered_words to return the raw text string with the gendered words highlighted via `<em></em>`.
