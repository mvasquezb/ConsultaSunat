#Printint Error File
from __future__ import print_function
import sys

def eprint(*args,**kwargs):
  print(*args, file = sys.stderr, **kwargs)

from Utils.message import MessageList

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

def read_url_from_file(temp_file):
	str = read_text_from_file(temp_file)

	if str is None:
		return None
	else:
		validate = URLValidator()
		try:
			validate(str)
		except ValidationError:
			return None

		return str


def read_text_from_file(temp_file):
	str = temp_file.readline().strip()

	# Soporta comentarios
	while str[0] == '#':
		str = temp_file.readline().strip()

	data = str.split('|')
  err = False

  if (len(data)!=3):
    return None
  else:
    return data[1]
    

def read_int_from_file(temp_file):
	str = read_text_from_file(temp_file)
	
	if str is None:
		return None
	else:
		try:
			return int(str)
		except:
			return None

def validate_tag_format(tag):
  tag_parts = tag.split()
  if len(tag_parts) is not 2:
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

def read_source_from_string(strdata, main_list = MessageList()):

  data = strdata.split('|')

  if (len(data)!=3):
    return None
  else:
      
    if validate_string_source(data[1]):
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
  return mystring and mystring.strip():
  
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

# Extracción de fechas de publicación de cada convocatoria de CAS
import json
import re
import dateparser
import datetime
from collections import namedtuple

PubDate = namedtuple('PubDate', ['month', 'year'])

ACCENTED = {
    'Á': 'A',
    'É': 'E',
    'Í': 'I',
    'Ó': 'O',
    'Ú': 'U',
    'Ñ': 'N',
}

def remove_accent(char):
    lower = char.islower()
    try:
        new_val = ACCENTED[char.upper()]
        if lower:
            new_val = new_val.lower()
        return new_val
    except KeyError:
        return char

def remove_accents(val, case='upper'):
    new_val = ''
    for char in val:
        if case == 'upper':
            char = char.upper()
        elif case == 'lower':
            char = char.lower()
        new_val += remove_accent(char)
    return new_val

def match_date(src):
    regex = re.compile('(\\d+([\\.|/])\\d+\\2\\d+)')
    match = regex.search(src)
    try:
        return match.group()
    except AttributeError:
        return None

def get_month_year(date_str):
    try:
        date = dateparser.parse(date_string=date_str)
        return PubDate(month=date.month, year=date.year)
    except:
        return None

def get_clean_date(src):
    date = match_date(src)
    if date is None:
        return None
    return get_month_year(date)

def get_match_group(src, pattern, matchNumber=0, groupNumber=1):
    #pattern = re.escape(pattern)
    try:
        matches = re.findall(pattern, src, re.IGNORECASE)
    except:
        return None

    if len(matches) == 0:
        return None

    match = matches[matchNumber]
    try:
        # Si hay varios grupos
        if isinstance(match, tuple):
            return match[groupNumber-1]
        # Si solo hay un grupo
        return match
    except:
        return None


def get_a_partir_del(src):
    regex = "a partir del?(.*?)[\.|,]"
    date_str = get_match_group(src,regex, groupNumber=2)
    
    if date_str is None:
        return None

    return get_month_year(date_str)

def get_desde_el(src):
    regex = "des?de\s+((el|ek)\s+)+(.*?)(\s+en|,|\.|desde|\n|\r)"
    date_str = get_match_group(src, regex, groupNumber=3)
    
    if date_str is None:
        return None

    return get_month_year(date_str)

def get_rango_fechas(src):
    regex = r"del \d+ al (\d+\s*.*?)[\.|,]"
    date_str = get_match_group(src, regex)

    if date_str is None:
        return None

    return get_month_year(date_str)

def get_publicacion_en(src):
    regex = "publicacion en [^:]*:\s+([^\.|,|\\n|\\r]*)"
    date_str = get_match_group(src, regex)

    if date_str is None:
        return None
    date = get_month_year(date_str)
    return date

# Ordenados por número de ocurrencias
FILTERS = [
    get_clean_date,
    get_a_partir_del,
    get_desde_el,
    get_rango_fechas,
    get_publicacion_en,
]

def get_date_from_description_CAS(desc):
    # Remueve tildes y convierte a mayúsculas
    desc = remove_accents(desc, case='upper')

    # Remueve requerimientos
    indexDetalle = desc.find("DETALLE:")
    if indexDetalle != -1:
        desc = desc[indexDetalle + len('DETALLE:'):].strip()

    # Remueve todo a partir de la cantidad de vacantes
    desc = re.compile("(CANTIDAD DE )?VACANTES:.*\n.*").sub('', desc).strip()

    # Pasa cada descripción por cada filtro de la lista hasta que la fecha sea válida
    fecha = None
    for func in FILTERS:
        fecha = func(desc)
        if fecha != None:
            break
    else:
        # Si no se encuentra la fecha, se asigna la del mes actual
        today = datetime.date.today()
        fecha = (today.month, today.year)

    return fecha
