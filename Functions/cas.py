import json
import re
import dateparser
import datetime
from collections import namedtuple

def make_area_urls(areas, url_base):
    """
    Generates url for specified area
    Not supported by CAS postings
    """
    return [url_base]

def make_period_url(period, url_base):
    """
    Generates url for specified period
    CAS: not supported, only returns base url
    """
    return url_base



def make_page_url(page_num, url_base):
    """
    Generates a url for the specified page number
    Unnecessary for CAS postings since the site loads all offers every time
    and just **shows** them using javascript
    """
    return url_base


def make_link_url(link, url_base):
    """
    Generates an offer's url using the relative one and a base
    """
    tokens = url_base.split('/')
    tokens[-1] = link
    return '/'.join(tokens)
        
# Publication date extraction for a CAS posting

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
        # Several capture groups
        if isinstance(match, tuple):
            return match[groupNumber-1]
        # Only one group
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

# Sorted by number of occurrences
FILTERS = [
    get_clean_date,
    get_a_partir_del,
    get_desde_el,
    get_rango_fechas,
    get_publicacion_en,
]

def to_publication_date(desc):
    # Remove accents and convert to uppercase
    desc = remove_accents(desc, case='upper')

    # Remove 'Requerimientos' section
    index_detalle = desc.find("DETALLE:")
    if index_detalle != -1:
        desc = desc[index_detalle + len('DETALLE:'):].strip()

    # Remove everything after 'DETALLE' section
    desc = re.compile("(CANTIDAD DE )?VACANTES:.*\n.*").sub('', desc).strip()

    # Apply each filter for the description until a date is found
    fecha = None
    for func in FILTERS:
        fecha = func(desc)
        if fecha != None:
            break
    else:
        # If no date is found, current one is assigned
        fecha = datetime.date.today()
    return fecha
