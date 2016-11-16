#Printint Error File
from __future__ import print_function
import sys

def eprint(*args,**kwargs):
  print(*args, file = sys.stderr, **kwargs)

from Utils.message import MessageList

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

def read_url_from_file(temp_file):
    str, optional = read_text_from_file(temp_file)

    if str is None:
        return None
    else:
        validate = URLValidator()
        try:
            validate(str)
        except ValidationError:
            return None

        return str, optional


def read_text_from_file(temp_file):
    str = temp_file.readline().strip()

    if str == '':
        return None, False
    
    # Soporta comentarios
    while str[0] == '#':
        str = temp_file.readline().strip()

    data = str.split('|')

    # parse text
    try:
        value = data[1]
    except:
        return None, False
    
    optional = value.startswith('optional')
    if optional:
        value = value[len('optional'):]
        value = value[1:] if value != '' else ''

    value = value if value != '' else None

    return value, optional

    

def read_int_from_file(temp_file):
    str, optional = read_text_from_file(temp_file)
    
    if str is None:
        return None, optional
    
    try:
        return int(str), optional
    except:
        return None, optional

def validate_tag_format(tag):
  tag_parts = tag.split()
  if len(tag_parts) != 2:
    return False
  else:
    index = tag_parts[0]
    return index.isdigit() or index == '*'


def validate_dictionary_format(dictionary):
  try:
    dictionary = eval(dictionary)
  except:
    return False

  return isinstance(dictionary, dict)

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

def read_source_from_string(data, main_list = MessageList()):
  if data is None:
      return None
      
  if validate_string_source(data):
    try:  
      list_data = eval(data)
      if type(list_data) is list:
        main_list.add_msg("Using list data from template: " + str(list_data),MessageList.INF)
        return list_data
    except:
      return None
        
  else:
    levels = data.split('->')
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

    return data


def read_source_from_file(temp_file):
  value, optional = read_text_from_file(temp_file)
  if value is None:
    return None, optional
  else:
    return read_source_from_string(value), optional
  


def is_blank(mystring):
  if mystring and mystring.strip():
      return False
  return True
  
def clean_whitespaces(text):
  return ' '.join(text.split())
