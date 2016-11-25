from selenium import webdriver
from selenium.common.exceptions import *
import contextlib
from PIL import Image
import pyocr
import requests

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
    try:
        driver.switch_to.frame(frame_elem)
        driver.save_screenshot('image.png')
        img_elem = driver.find_element_by_xpath(img_xpath)
    except NoSuchElementException:
        print("Element", img_xpath, "not found")
        return ''

    loc = img_elem.location
    size = img_elem.size
    captcha = get_subimage('image.png', loc, size)
    captcha.save('captcha.png')

    return captcha

def get_captcha_text(driver, frame_elem):
    captcha = get_captcha_image(driver, frame_elem)
    if not captcha:
        return ''
    return get_text_from_image(captcha)

def get_data_by_ruc(driver, search_frame, ruc, captcha):
    ruc_input = search_frame.find_element_by_name('search1')
    captcha_input = search_frame.find_element_by_name('codigo')
    

def main():
    url_sunat = 'http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias'
    search_frame_xpath = '//frame[@src="frameCriterioBusqueda.jsp"]'

    with browse(webdriver.PhantomJS()) as driver:
        driver.get(url_sunat)
        try:
            search_frame = driver.find_element_by_xpath(search_frame_xpath)
        except Exception as e:
            print(e)
            exit(1)
        captcha = get_captcha_text(driver, search_frame)
        print("Text in captcha:", captcha)
        if not captcha:
            print("Error reading captcha")
            exit(1)

        driver.switch_to_default_content()
        
        ruc = '20331066703'
        try:
            data = get_data_by_ruc(driver, search_frame, ruc, captcha)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()