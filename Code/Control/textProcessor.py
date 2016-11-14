from nltk.corpus import stopwords
import codecs
import string
import treetaggerwrapper
import re

from nltk.stem.snowball import SpanishStemmer


punctuations = '¡!"#$%&\'()*+,-⁻./:;<=>?[\\]^_`{|}~• ' #@ not included (@risk)
spanish_stemmer = SpanishStemmer()
stop_spanish = stopwords.words('spanish')
stop_english = stopwords.words('english')
non_special_characters_spanish = '[^a-zA-Z0-9áéíóúñ ]'


def preprocess(text):
  text = text.lower()
  text = re.sub(non_special_characters_spanish,' ', text) #remove punctuations
  text = remove_whitespaces(text)
  return text


def remove_numbers(text):
  return ''.join([char for char in text if not char.isdigit()])


def remove_punctuation(text):
  regex = re.compile('[%s]' % re.escape(string.punctuation))
  return regex.sub(' ',text)


def remove_whitespaces(text):
  return ' '.join(text.split())


def remove_stopwords(text):
  words = []
  for word in text.split():
    if word not in stop_spanish:
      words.append(word)

  new_text = ' '.join(words)
  return new_text


def stem(text):
  stem_words = []
  for word in text.split():
    word = spanish_stemmer.stem(word)
    stem_words.append(word)

  stem_text = ' '.join(stem_words)
  return stem_text


