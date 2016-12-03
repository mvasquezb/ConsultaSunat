from selenium import webdriver
from selenium.common.exceptions import *
import contextlib
from PIL import Image
import pyocr
import requests
import bs4
import sys
import re
import collections
import logging
import logging.config
from datetime import datetime
import json

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('sunat')

"""
Tipo CIIU que define una actividad economica de un contribyente
"""
CIIU = collections.namedtuple('CIIU', ['cod', 'desc', 'rev'])

DeudaCoactiva = collections.namedtuple('DeudaCoactiva', ['monto', 'periodo_tributario', 'fecha_inicio', 'entidad_asociada'])

url_base = 'http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/'
url_consulta = url_base + 'jcrS00Alias'

class SunatJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, datetime):
            return json.dumps(obj, ensure_ascii=False, indent=2)
        return [
            obj.year,
            obj.month,
            obj.day
        ]


@contextlib.contextmanager
def browse(driver):
    yield driver
    driver.quit()

def get_subimage(source, loc, size):
    img = Image.open(source)

    left = loc['x']
    top = loc['y']
    right = loc['x'] + size['width']
    bottom = loc['y'] + size['height']

    img = img.crop((left, top, right, bottom))

    return img

def get_text_from_image(image):
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        logger.error("No OCR tool found")
        raise ValueError("No OCR tool found")

    tool = tools[0]

    return tool.image_to_string(image)

def get_captcha_image(driver, frame_elem):
    img_xpath = '//img[@src="captcha?accion=image"]'
    driver.switch_to.frame(frame_elem)

    driver.save_screenshot('image.png')
    img_elem = driver.find_element_by_xpath(img_xpath)

    loc = img_elem.location
    size = img_elem.size
    captcha = get_subimage('image.png', loc, size)
    captcha.save('captcha.png')
    driver.switch_to_default_content()

    return captcha

def get_captcha_text(driver, frame_elem):
    captcha = get_captcha_image(driver, frame_elem)
    return get_text_from_image(captcha)

def save_results(driver, filename):
    result_frame = driver.find_element_by_xpath('//frame[@src="frameResultadoBusqueda.html"]')
    driver.switch_to.frame(result_frame)
    source = driver.page_source
    with open(filename, 'w') as f:
        f.write(source)
    driver.switch_to_default_content()

def get_ruc_nombre_contribuyente(soup):
    """
    Gets the RUC and name (not commercial) of the taxpayer
    Any exception should propagate upwards
    """
    tag = soup.find('td', {'class':'bgn'}, text=re.compile('n[ú|u]mero\s+de\s+ruc:\s+', re.IGNORECASE))
    ruc_tag = tag.find_next('td')
    text = ruc_tag.get_text()

    tokens = text.split('-')
    try:
        ruc = int(tokens[0])
    except ValueError:
        raise ValueError("Couldn't obtain RUC value from string: " + tokens[0])
    except IndexError:
        raise IndexError("Not enough tokens to get RUC: " + str(tokens))

    text = '-'.join(tokens[1:])

    return ruc, text.strip()

def get_nombre_comercial_contribuyente(soup):
    tag = soup.find('td', {'class':'bgn'}, text=re.compile('nombre\s+comercial:\s*', re.IGNORECASE))
    nombre_tag = tag.find_next('td')
    return nombre_tag.get_text().strip()

def get_estado_contribuyente(soup):
    tag = soup.find('td', {'class':'bgn'}, text=re.compile('estado\s+del?\s+contribuyente:\s*', re.IGNORECASE))
    estado_tag = tag.find_next('td')
    return estado_tag.get_text().strip()

def get_condicion_contribuyente(soup):
    tag = soup.find('td', {'class':'bgn'}, text=re.compile('condici[ó|o]n\s+del\s+contribuyente:\s*', re.IGNORECASE))
    cond_tag = tag.find_next('td')
    return cond_tag.get_text().strip()

def clean_ciiu_str(ciiu_str):
    tokens = [ token.strip() for token in ciiu_str.split('-') ]

    desc = tokens[-1]
    codigo = tokens[-2]

    if codigo.startswith('CIIU'):
        codigo = codigo[len('CIIU'):]
    codigo = int(codigo)

    return (codigo, desc)

def get_ciiu_in_comments(soup):
    comments = comments=soup.find_all(string=lambda text: isinstance(text, bs4.Comment))
    
    ciiu = []
    indexSelect = -1
    selectEnd = False
    for index, com in enumerate(comments):
        if indexSelect == -1 and '<select name="select"' in com:
            indexSelect = index
        
        if indexSelect != -1 and not selectEnd:
            if '<option' in com:
                com_soup = bs4.BeautifulSoup(com, 'lxml')
                ciiu.append(com_soup.get_text().strip())
            elif '</select>' in com:
                selectEnd = True

    ciiu = [ clean_ciiu_str(ci) for ci in ciiu ]
    ciiu = [ CIIU(ci[0], ci[1], 3) for ci in ciiu ]

    return ciiu

def get_ciiu_revision(ciiu_list):
    revision_3 = [ ci.cod for ci in ciiu_list if type(ci) is CIIU ]
    to_delete = []
    for index, ci in enumerate(ciiu_list):
        if type(ci) is not CIIU and ci[0] not in revision_3:
            ciiu_list[index] = CIIU(ci[0], ci[1], 4)


def get_ciiu_contribuyente(soup):
    ciiu = []
    comments = get_ciiu_in_comments(soup)
    ciiu += comments
    
    select = soup.find('select', {'name':'select'})
    options = select.find_all('option')
    options = [ clean_ciiu_str(op.get_text()) for op in options ]
    ciiu += options

    get_ciiu_revision(ciiu)
    ciiu = list(filter(lambda x: type(x) is CIIU, ciiu))
    return ciiu

def get_extended_info_attr(params, accion, func_from_row):
    if not isinstance(params, collections.Mapping):
        raise TypeError("params is not dictionary")
    if type(accion) is not str:
        raise TypeError("accion is not string")
    if not callable(func_from_row):
        raise TypeError("func_from_row is not callable")

    params['accion'] = accion
    try:
        res = requests.get(url_consulta, params, timeout=5)
    except requests.exceptions.Timeout:
        raise TimeoutException("Couldn't connect to {accion} within {time} seconds".format(accion, 5))
    soup = bs4.BeautifulSoup(res.text, 'lxml')

    # First table for the title, second for the results of the query
    tables = soup.find_all('table')
    results_table = tables[1]
    intro_cell = results_table.find('td', {'class': 'bgn'})
    
    attr_list = []
    if intro_cell.get_text().strip().startswith('No'):
        # There are no records
        return attr_list

    # There are records
    debt_table = results_table.find('table').find('table')
    # Discard header row
    rows = debt_table.find_all('tr')[1:]
    
    # Check if table only has error message (case with 'Actas Probatorias')
    if rows[0].find('td').get_text().strip().startswith('No'):
        return attr_list

    # Everything is fine, continue parsing
    for row in rows:
        attr_list.append(func_from_row(row))

    return attr_list

def get_deuda_from_row(row):
    values = [ cell.get_text().strip() for cell in row.find_all('td') ]
    
    if len(values) != 4:
        raise ValueError("Incorrect number of attributes for '{name}' record".format(name='Deuda Coactiva'))

    monto = float(values[0])
    periodo_tributario = values[1]
    periodo_tributario = tuple([ int(val) for val in periodo_tributario.split('-') ])
    fecha = datetime.strptime(values[2], "%d/%m/%Y")
    entidad_asociada = values[3]

    return DeudaCoactiva(monto, periodo_tributario, fecha, entidad_asociada)

def get_ot_from_row(row):
    values = [ cell.get_text().strip() for cell in row.find_all('td') ]

    if len(values) != 2:
        raise ValueError("Incorrect number of attributes for '{name}' record".format(name='Omision Tributaria'))

    periodo_tributario = values[0]
    periodo_tributario = tuple([ int(val) for val in periodo_tributario.split('-') ])
    tributo = values[1]

    return (periodo_tributario, tributo)

def get_acta_prob_from_row(row):
    values = [ cell.get_text().strip() for cell in row.find_all('td') ]

    if len(values) != 2:
        raise ValueError("Incorrect number of attributes for '{name}' record".format(name='Acta Probatoria'))

    num_acta = int(values[0])
    fecha = datetime.strptime(values[1], '%d/%m/%Y')
    lugar = values[2]
    infraccion = values[3]
    desc_infraccion = values[4]
    ri_roz = values[5]
    acta_recon = values[6]

    return (num_acta, fecha, lugar, infraccion, desc_infraccion, ri_roz, acta_recon)

def get_deuda_coactiva_contribuyente(params):
    deudas = get_extended_info_attr(params, 'getInfoDC', get_deuda_from_row)
    return deudas

def get_omision_tributaria_contribuyente(params):
    ot = get_extended_info_attr(params, 'getInfoOT', get_ot_from_row)
    return ot
"""
# NOT WORKING: Requires too much customization for now
def get_acta_probatoria_contribuyente(params):
    actas = get_extended_info_attr(params, 'getActPro', get_acta_prob_from_row)
    return actas
"""
def add_extended_info(data):
    """
    Get data hidden through buttons
    """
    if data is None:
        return None

    params = {
        'nroRuc': data['ruc'],
        'desRuc': data['nombre'],
    }
    data['deuda_coactiva'] = get_deuda_coactiva_contribuyente(params)
    data['omision_tributaria'] = get_omision_tributaria_contribuyente(params)

def parse_results_file(filename):
    with open(filename, 'r') as f:
        text = f.read()
    html = bs4.BeautifulSoup(text, "lxml")

    error = html.find('p', {'class': 'error'})
    if error is not None:
        raise AttributeError(error.get_text())

    data = {}

    data['ruc'], data['nombre'] = get_ruc_nombre_contribuyente(html)
    data['nombre_comercial'] = get_nombre_comercial_contribuyente(html)
    data['estado'] = get_estado_contribuyente(html)
    data['condicion'] = get_condicion_contribuyente(html)
    data['ciiu'] = get_ciiu_contribuyente(html)

    return data

def get_data_by_ruc(driver, search_frame, ruc, captcha):
    driver.switch_to.frame(search_frame)
    try:
        ruc_input = driver.find_element_by_xpath('//input[@name="search1"]')
        captcha_input = driver.find_element_by_xpath('//input[@name="codigo"]')
        submit_btn = driver.find_element_by_xpath('//input[@value="Buscar"]')
    except NoSuchElementException as e:
        raise NoSuchElementException(eval(e.msg)['errorMessage'])

    ruc_input.send_keys(str(ruc))
    captcha_input.send_keys(str(captcha))
    submit_btn.click()
    driver.save_screenshot('image2.png')
    driver.implicitly_wait(10)

    driver.switch_to_default_content()

    save_results(driver, 'frame.xml')

    data = parse_results_file('frame.xml')

    add_extended_info(data)

    return data

def main():
    search_frame_xpath = '//frame[@src="frameCriterioBusqueda.jsp"]'

    # User defined
    #ruc = '20331066703'
    #ruc = '20141528069'
    ruc = '20159253539'
    #ruc = '20217932565'
    max_retries = 5
    filename = 'resultado.txt'

    retry = True
    num_retries = 0
    with browse(webdriver.PhantomJS()) as driver:
        driver.set_page_load_timeout(5)
        while retry and num_retries < max_retries:
            num_retries += 1
            try:
                driver.get(url_consulta)
            except TimeoutException:
                logger.error("Page load timed out")
                logger.info('Waiting before retry...')
                driver.implicitly_wait(5)
                continue

            try:
                search_frame = driver.find_element_by_xpath(search_frame_xpath)
            except NoSuchElementException as e:
                logger.error("Incorrect xpath for search frame: %s", search_frame_xpath)
                continue

            captcha = get_captcha_text(driver, search_frame)
            logger.info("Text in captcha: %s", captcha)
            if not captcha or len(captcha) != 4:
                logger.error("Error reading captcha: %s", captcha)
                continue
            
            data = None
            try:
                data = get_data_by_ruc(driver, search_frame, ruc, captcha)
            except Exception as e:
                logger.error(e)
                continue

            with open(filename, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, cls=SunatJSONEncoder)
            retry = False
            logger.info("Request finished successfully. Results saved to: %s", filename)
        
        if num_retries >= max_retries:
            logger.info("Max number of retries reached. Exiting...")


if __name__ == '__main__':
    main()