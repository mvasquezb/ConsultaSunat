import json
import re
import dateparser
import datetime
from collections import namedtuple

def make_area_urls(areas, url_base):
    """
    Genera una lista de links de cada área
    Como Centro de Empleo no soporta áreas, solo se devuelve el base
    """
    return [url_base]

def make_period_url(period, url_base):
    """
    Genera un link para el periodo especificado
    Como Centro de Empleo no soporta periodos, solo se devuelve el base
    """
    return url_base



def make_page_url(page_num, url_base):
    """
    Genera un link para la página especificada
    Como Centro de Empleo carga todas las convocatorias de inmediato,
    no es necesario
    """
    return url_base


def make_link_url(link, url_base):
    """
    Genera el link absoluto de una oferta a partir del relativo y la base
    """
    tokens = url_base.split('/')
    tokens[-1] = link
    return '/'.join(tokens)
        
# Extracción de fechas de publicación de cada convocatoria de CAS

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
    regex = r"a partir del?(.*?)[\.|,]"
    date_str = get_match_group(src, regex, groupNumber=2)
    
    if date_str is None:
        return None

    return get_month_year(date_str)

def get_desde_el(src):
    regex = r"des?de\s+((el|ek)\s+)+(.*?)(\s+en|,|\.|desde|\n|\r)"
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
    index_detalle = desc.find("DETALLE:")
    if index_detalle != -1:
        desc = desc[index_detalle + len('DETALLE:'):].strip()

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
        fecha = datetime.date.today()
    return fecha

#TODO: to_publication_date()
