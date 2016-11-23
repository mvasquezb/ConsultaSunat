from selenium import webdriver
import contextlib

@contextlib.contextmanager
def browse(driver):
    yield driver
    driver.quit()

with browse(webdriver.Firefox()) as driver:
    driver.get('http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias')
    driver.save_screenshot('image.png')