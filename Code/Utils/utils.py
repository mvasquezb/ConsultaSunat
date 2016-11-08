#Printint Error File
from __future__ import print_function
import sys

def eprint(*args,**kwargs):
  print(*args, file = sys.stderr, **kwargs)

from Utils.message import MessageList

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

def read_url_from_file(temp_file):
  str = temp_file.readline()
  data = str.split('|')

  err = False
  if (len(data)!=3):
    return None
  else:
    validate = URLValidator()
    try:
      validate(data[1])
    except ValidationError:
      return None

    return data[1]


def read_text_from_file(temp_file):
  str = temp_file.readline()
  data = str.split('|')

  err = False

  if (len(data)!=3):
    return None
  else:
    return data[1]
    

def read_int_from_file(temp_file):
  str = temp_file.readline()
  data = str.split('|')

  err = False
  if(len(data)!=3):
    return None
  else:
    try:
      val = int(data[1])
    except:
      return None
    return val


def validate_tag_format(tag):
  tag_parts = tag.split()
  if len(tag_parts) is not 2:
    return False
  else:
    index = tag_parts[0]
    if index.isdigit() or index == '*':
      return True
    else:
      return False


def validate_dictionary_format(dictionary):
  try:
    dictionary = eval(dictionary)
  except:
    return False

  if type(dictionary) is dict:
    return True
  else:
    return False

def validate_attribute_format(attr):
  return attr.isalpha() or attr == ""


def validate_string_source(source):

  if source is "":
    return False

  nlvls = len(source.split('->'))
  if (nlvls == 1):
    nparts = len(source.split('\\'))
    if nparts == 1:
      return True
    else:
      return False
  else:
    return False



def read_source_from_string(strdata ,main_list = MessageList() ):


  data = strdata.split('|')

  if (len(data)!=3):
    return None
  else:
      
    if validate_string_source(data[1]):
      list_data = eval(data[1])
      if type(list_data) is list:
        main_list.add_msg("Using list data from template: " + str(list_data),MessageList.INF)
        return list_data

      try:  
        list_data = eval(data[1])
        if type(list_data) is list:
          main_list.add_msg("Using list data from template: " + str(list_data),MessageList.INF)
          return list_data

      except:
        return None

        
    else:

      levels = data[1].split('->')
      for level in levels:
        parts = level.split('\\')

        if (len(parts)!=3):
          return None
        else:
          
          tag = parts[0]
          if not validate_tag_format(tag):
            return None

          dicc = parts[1]
          if not validate_dictionary_format(dicc):
            return None

          attr = parts[2]
          if not validate_attribute_format(attr):
            return None

      return data[1]


def read_source_from_file(temp_file):
  fileline = temp_file.readline()
  if fileline is None:
    return None
  else:
    return read_source_from_string(fileline)
  


def is_blank(mystring):
  if mystring and mystring.strip():
    return False
  return True
  
#def stemText(self,text):
#  newText = ""
#  for word in text.split():
#    wordStemmed = Processor.STEMMER.stem(word)
#    newText += wordStemmed + ' '
#
#  return newText.strip()
#
#
def clean_whitespaces(text):
  return ' '.join(text.split())


