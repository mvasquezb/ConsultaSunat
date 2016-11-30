from selenium import webdriver
from selenium.common.exceptions import *
import contextlib
from PIL import Image
import pyocr
import requests
import bs4
import sys
import re
from collections import namedtuple

"""
Tipo CIIU que define una actividad economica de un contribyente
"""
CIIU = namedtuple('CIIU', ['codigo', 'desc', 'rev'])

DeudaCoactiva = namedtuple('DeudaCoactiva', ['monto', 'periodo_tributario', 'fecha_inicio', 'entidad_asociada'])

url_sunat = 'http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias'

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
        print("No OCR tool found")
        exit(1)

    tool = tools[0]

    return tool.image_to_string(image)

def get_captcha_image(driver, frame_elem):
    img_xpath = '//img[@src="captcha?accion=image"]'
    driver.switch_to.frame(frame_elem)
    try:
        driver.save_screenshot('image.png')
        img_elem = driver.find_element_by_xpath(img_xpath)
    except NoSuchElementException as e:
        print(e)
        return ''

    loc = img_elem.location
    size = img_elem.size
    captcha = get_subimage('image.png', loc, size)
    captcha.save('captcha.png')
    driver.switch_to_default_content()

    return captcha

def get_captcha_text(driver, frame_elem):
    captcha = get_captcha_image(driver, frame_elem)
    if not captcha:
        return ''
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
    return ciiu

def get_ciiu_contribuyente(soup):
    ciiu = []
    comments = get_ciiu_in_comments(soup)
    ciiu += comments
    
    select = soup.find('select', {'name':'select'})
    options = select.find_all('option')
    options = [ clean_ciiu_str(op.get_text()) for op in options ]
    ciiu += options

    return ciiu

def get_deuda_from_row(row):
    cells = [cell.get_text().strip() for cell in row.find_all('td')]
    
    monto = float(cells[0])
    periodo_tributario = cells[1]
    fecha_inicio = cells[2]
    entidad_asociada = cells[3]

    return DeudaCoactiva(monto, periodo_tributario, fecha_inicio, entidad_asociada)

def get_deuda_coactiva_contribuyente(params):
    params['accion'] = 'getInfoDC'
    res = requests.get(url_sunat, params)
    soup = bs4.BeautifulSoup(res.text, 'lxml')

    # First table for the title, second for the results of the query
    tables = soup.find_all('table')
    results_table = tables[1]
    print(results_table)
    intro_cell = results_table.find('td', {'class': 'bgn'})

    deudas = []
    if intro_cell.get_text().strip().startswith('No'):
        # There are no debts
        return deudas

    # There are debts
    debt_table = results_table.find('table').find('table')
    # Discard header row
    rows = debt_table.find_all('tr')[1:]
    for row in rows:
        deudas.append(get_deuda_from_row(row))
    return deudas

def add_hidden_data(data):
    """
    Get data hidden through buttons
    """
    params = {
        'nroRuc': data['ruc'],
        'desRuc': data['nombre'],
    }
    data['deuda_coactiva'] = get_deuda_coactiva_contribuyente(params)

def parse_results_file(filename):
    with open(filename, 'r') as f:
        text = f.read()
    html = bs4.BeautifulSoup(text, "lxml")

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
        print(e)
        return None

    ruc_input.send_keys(str(ruc))
    captcha_input.send_keys(str(captcha))
    submit_btn.click()
    driver.save_screenshot('image2.png')
    driver.implicitly_wait(10)

    driver.switch_to_default_content()

    save_results(driver, 'frame.xml')

    data = parse_results_file('frame.xml')

    add_hidden_data(data)

    return data

def main():
    search_frame_xpath = '//frame[@src="frameCriterioBusqueda.jsp"]'

    with browse(webdriver.PhantomJS()) as driver:
        driver.get(url_sunat)
        try:
            search_frame = driver.find_element_by_xpath(search_frame_xpath)
        except NoSuchElementException as e:
            print(e)
            return

        captcha = get_captcha_text(driver, search_frame)
        print("Text in captcha:", captcha)
        if not captcha or len(captcha) != 4:
            print("Error reading captcha")
            return
        
        #ruc = '20331066703'
        #ruc = '20141528069'
        ruc = '20159253539'
        data = None
        try:
            data = get_data_by_ruc(driver, search_frame, ruc, captcha)
        except NoSuchElementException as e:
            print(e)

        print(data)

if __name__ == '__main__':
    main()