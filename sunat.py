from selenium import webdriver
from selenium.common.exceptions import *
from PIL import Image
import pyocr
import requests
import bs4
import sys
import re
import collections
import datetime
from utils import (
    CIIU,
    DeudaCoactiva
)

class Sunat:
    def __init__(self, web_driver, logger):
        self.web_driver = web_driver
        self.logger = logger
        self.url_consulta = 'http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias'

    def get_subimage(self, source, loc, size):
        img = Image.open(source)

        left = loc['x']
        top = loc['y']
        right = loc['x'] + size['width']
        bottom = loc['y'] + size['height']

        img = img.crop((left, top, right, bottom))

        return img

    def get_text_from_image(self, image):
        tools = pyocr.get_available_tools()
        if len(tools) == 0:
            self.logger.error("No OCR tool found")
            raise ValueError("No OCR tool found")

        tool = tools[0]

        return tool.image_to_string(image)

    def get_captcha_image(self, frame_elem):
        img_xpath = '//img[@src="captcha?accion=image"]'
        self.web_driver.switch_to.frame(frame_elem)

        self.web_driver.save_screenshot('image.png')
        img_elem = self.web_driver.find_element_by_xpath(img_xpath)

        loc = img_elem.location
        size = img_elem.size
        captcha = self.get_subimage('image.png', loc, size)
        captcha.save('captcha.png')
        self.web_driver.switch_to_default_content()

        return captcha

    def get_captcha_text(self, frame_elem):
        captcha = self.get_captcha_image(frame_elem)
        return self.get_text_from_image(captcha)

    def save_results(self, filename):
        result_frame = self.web_driver.find_element_by_xpath('//frame[@src="frameResultadoBusqueda.html"]')
        self.web_driver.switch_to.frame(result_frame)
        source = self.web_driver.page_source
        with open(filename, 'w') as f:
            f.write(source)
        self.web_driver.switch_to_default_content()

    def get_ruc_nombre_contribuyente(self, soup):
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

    def get_nombre_comercial_contribuyente(self, soup):
        tag = soup.find('td', {'class':'bgn'}, text=re.compile('nombre\s+comercial:\s*', re.IGNORECASE))
        nombre_tag = tag.find_next('td')
        return nombre_tag.get_text().strip()

    def get_estado_contribuyente(self, soup):
        tag = soup.find('td', {'class':'bgn'}, text=re.compile('estado\s+del?\s+contribuyente:\s*', re.IGNORECASE))
        estado_tag = tag.find_next('td')
        return estado_tag.get_text().strip()

    def get_condicion_contribuyente(self, soup):
        tag = soup.find('td', {'class':'bgn'}, text=re.compile('condici[ó|o]n\s+del\s+contribuyente:\s*', re.IGNORECASE))
        cond_tag = tag.find_next('td')
        return cond_tag.get_text().strip()

    def get_ciiu_in_comments(self, soup):
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

        ciiu = [ CIIU.from_string(ci) for ci in ciiu ]

        return ciiu

    def get_clean_ciiu_list(self, ciiu_comments, ciiu_options):
        clean_ciiu = []
        
        for index, ci in enumerate(ciiu_options):
            if ci not in ciiu_comments:
                ci.revision = 4
                clean_ciiu.append(ci)
        clean_ciiu += ciiu_comments
        return clean_ciiu

    def get_ciiu_contribuyente(self, soup):
        ciiu = []
        comments = self.get_ciiu_in_comments(soup)
        
        select = soup.find('select', {'name':'select'})
        options = select.find_all('option')
        options = [ CIIU.from_string(op.get_text()) for op in options ]

        ciiu = self.get_clean_ciiu_list(comments, options)
        return ciiu

    def get_extended_info_attr(self, params, accion, func_from_row):
        if not isinstance(params, collections.Mapping):
            raise TypeError("params is not dictionary")
        if type(accion) is not str:
            raise TypeError("accion is not string")
        if not callable(func_from_row):
            raise TypeError("func_from_row is not callable")

        params['accion'] = accion
        try:
            print(params)
            res = requests.get(self.url_consulta, params, timeout=5)
        except requests.exceptions.Timeout as e:
            print(e)
            raise TimeoutException("Couldn't connect to {action} within {time} seconds".format(action=accion, time=5))
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

    def get_deuda_from_row(self, row):
        values = [ cell.get_text().strip() for cell in row.find_all('td') ]
        
        if len(values) != 4:
            raise ValueError("Incorrect number of attributes for '{name}' record".format(name='Deuda Coactiva'))

        monto = float(values[0])
        periodo_tributario = datetime.date(*[ int(val) for val in values[1].split('-') ], 1)
        fecha = datetime.datetime.strptime(values[2], "%d/%m/%Y")
        entidad_asociada = values[3]

        return DeudaCoactiva(monto, periodo_tributario, fecha, entidad_asociada)

    def get_ot_from_row(self, row):
        values = [ cell.get_text().strip() for cell in row.find_all('td') ]

        if len(values) != 2:
            raise ValueError("Incorrect number of attributes for '{name}' record".format(name='Omision Tributaria'))

        periodo_tributario = values[0]
        periodo_tributario = datetime.date(*[ int(val) for val in periodo_tributario.split('-') ])
        tributo = values[1]

        return (periodo_tributario, tributo)

    def get_acta_prob_from_row(self, row):
        values = [ cell.get_text().strip() for cell in row.find_all('td') ]

        if len(values) != 2:
            raise ValueError("Incorrect number of attributes for '{name}' record".format(name='Acta Probatoria'))

        num_acta = int(values[0])
        fecha = datetime.datetime.strptime(values[1], '%d/%m/%Y')
        lugar = values[2]
        infraccion = values[3]
        desc_infraccion = values[4]
        ri_roz = values[5]
        acta_recon = values[6]

        return (num_acta, fecha, lugar, infraccion, desc_infraccion, ri_roz, acta_recon)

    def get_deuda_coactiva_contribuyente(self, params):
        deudas = self.get_extended_info_attr(params, 'getInfoDC', self.get_deuda_from_row)
        return deudas

    def get_omision_tributaria_contribuyente(self, params):
        ot = self.get_extended_info_attr(params, 'getInfoOT', self.get_ot_from_row)
        return ot
    """
    # NOT WORKING: Requires too much customization for now
    def get_acta_probatoria_contribuyente(params):
        actas = get_extended_info_attr(params, 'getActPro', get_acta_prob_from_row)
        return actas
    """
    def get_extended_information(self, ruc, nombre):
        """
        Get data hidden through buttons
        """
        params = {
            'nroRuc': ruc,
            'desRuc': nombre,
        }
        data = {}
        data['deuda_coactiva'] = self.get_deuda_coactiva_contribuyente(params)
        data['omision_tributaria'] = self.get_omision_tributaria_contribuyente(params)
        return data

    def parse_results_file(self, filename):
        with open(filename, 'r') as f:
            text = f.read()
        html = bs4.BeautifulSoup(text, "lxml")

        error = html.find('p', {'class': 'error'})
        if error is not None:
            raise AttributeError(error.get_text())

        data = {}

        data['ruc'], data['nombre'] = self.get_ruc_nombre_contribuyente(html)
        data['nombre_comercial'] = self.get_nombre_comercial_contribuyente(html)
        data['estado'] = self.get_estado_contribuyente(html)
        data['condicion'] = self.get_condicion_contribuyente(html)
        data['ciiu'] = self.get_ciiu_contribuyente(html)

        return data

    def get_search_frame(self, driver):
        search_frame_xpath = '//frame[@src="frameCriterioBusqueda.jsp"]'
        try:
            search_frame = driver.find_element_by_xpath(search_frame_xpath)
            return search_frame
        except NoSuchElementException as e:
            raise NoSuchElementException(eval(e.msg)['errorMessage'])

    def solve_captcha(self, driver):
        search_frame = self.get_search_frame(driver)
        captcha = self.get_captcha_text(search_frame)
        self.logger.info("Text in captcha: %s", captcha)
        if not captcha or len(captcha) != 4:
            raise ValueError("Error reading captcha: {}".format(captcha))
        return captcha

    def get_basic_information(self, ruc):
        self.web_driver.get(self.url_consulta)
        captcha = self.solve_captcha(self.web_driver)
        search_frame = self.get_search_frame(self.web_driver)
        self.web_driver.switch_to.frame(search_frame)
        try:
            ruc_input = self.web_driver.find_element_by_xpath('//input[@name="search1"]')
            captcha_input = self.web_driver.find_element_by_xpath('//input[@name="codigo"]')
            submit_btn = self.web_driver.find_element_by_xpath('//input[@value="Buscar"]')
        except NoSuchElementException as e:
            raise NoSuchElementException(eval(e.msg)['errorMessage'])

        ruc_input.send_keys(str(ruc))
        captcha_input.send_keys(str(captcha))
        submit_btn.click()
        self.web_driver.implicitly_wait(10)
        self.web_driver.switch_to_default_content()

        self.save_results('frame.xml')

        data = self.parse_results_file('frame.xml')
        return data

    def get_all_information(self, ruc):
        try:
            basic_data = self.get_basic_information(ruc)
            ext_data = self.get_extended_information(ruc, basic_data['nombre'])
            data = {}
            data.update(basic_data)
            data.update(ext_data)
            return data
        except TimeoutException:
            self.logger.error("Page load timed out")
            self.logger.info('Waiting before retry...')
            self.web_driver.implicitly_wait(5)
            return None
        except Exception as e:
            self.logger.error(e)
            return None
        finally:
            self.web_driver.switch_to_default_content()
