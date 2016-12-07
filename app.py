from selenium import webdriver
import contextlib
import logging
import logging.config
import datetime
import tempfile
import argparse
import json
from sunat import Sunat
from utils import CustomJSONEncoder

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('sunat')

arg_parser = argparse.ArgumentParser(
    description="Get RUC information through SUNAT"
)
# Only one for now
arg_parser.add_argument(
    'ruc', 
    nargs='+', 
    type=int, 
    #help='Lista de RUCs con los cuales realizar las consultas',
    help='RUC to query SUNAT with',
)
arg_parser.add_argument(
    '--retries',
    type=int,
    default=5,
    help='Limit number of retries'
)
arg_parser.add_argument(
    '-o',
    '--outfile',
    default='sunat-results.txt',
    help='Where to save the results'
)

@contextlib.contextmanager
def browse(driver):
    yield driver
    driver.quit()

def main():
    args = arg_parser.parse_args()
    # User defined
    #ruc_list = [20331066703, 20141528069, 20159253539, 20217932565]
    ruc_list = args.ruc
    max_retries = args.retries
    outfile = args.outfile
    
    with browse(webdriver.PhantomJS()) as driver:
        driver.set_page_load_timeout(5)
        sunat = Sunat(driver, logger)
        all_data = []
        for ruc in ruc_list:
            retry = True
            num_retries = 0
            while retry and num_retries < max_retries:
                num_retries += 1
                data = sunat.get_all_information(ruc)
                if data is not None:
                    all_data.append(data)
                    retry = False

            if num_retries >= max_retries:
                logger.info("Max number of retries reached. Exiting...")

        with open(outfile, 'w') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)

        if len(all_data) < len(ruc_list):
            logger.info("Couldn't complete request for some or all RUC values. Results saved to: %s", outfile)
        else:
            logger.info("Request finished successfully. Results saved to: %s", outfile)

if __name__ == '__main__':
    main()