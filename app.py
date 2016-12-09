from selenium import webdriver
import contextlib
import logging
import logging.config
import argparse
import json
import sys
from ConsultaSunat.sunat import Sunat
from ConsultaSunat.utils import CustomJSONEncoder
import os 

dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'
logging.config.fileConfig(dir_path + 'logging.conf')
logger = logging.getLogger('sunat')

def argparse_setup():
    arg_parser = argparse.ArgumentParser(
        description="Get RUC information through SUNAT"
    )
    group = arg_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--ruc', 
        nargs='+', 
        type=int, 
        help='RUC list to query SUNAT with',
    )
    group.add_argument(
        '--test',
        action='store_true',
        help='Test run. Overrides previously declared arguments'
    )
    arg_parser.add_argument(
        '--retries',
        type=int,
        default=-1,
        help='Limit number of retries. Default: indefinite'
    )
    arg_parser.add_argument(
        '-o',
        '--outfile',
        default='sunat-results.txt',
        help='Where to save the results'
    )

    return arg_parser

@contextlib.contextmanager
def browse(driver):
    yield driver
    driver.quit()

def main(argv=None):
    arg_parser = argparse_setup()
    args = arg_parser.parse_args(argv)

    # User defined
    ruc_list = args.ruc
    max_retries = args.retries
    outfile = args.outfile
    
    if args.test:
        ruc_list = [20331066703, 20141528069, 20159253539, 20217932565]
        outfile = 'sunat-search-test.txt'

    all_data = []
    with browse(webdriver.PhantomJS()) as driver:
        driver.set_page_load_timeout(5)
        sunat = Sunat(driver, logger)

        for ruc in ruc_list:
            logger.info("Started request for RUC: %d", ruc)
            retry = True
            num_retries = 0
            # If max_retries is not specified, there will be indefinite attempts
            while retry and (max_retries == -1 or num_retries < max_retries):
                num_retries += 1
                data = sunat.get_all_information(ruc)
                if data is not None:
                    all_data.append(data)
                    retry = False

            if num_retries >= max_retries and max_retries != -1:
                logger.info("Max number of retries reached.")
                logger.info("Request for RUC: %d failed", ruc)
            else:
                logger.info("Request for RUC %d completed successfully", ruc)

        with open(outfile, 'w') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)

        if len(all_data) < len(ruc_list):
            logger.info("Couldn't complete request for some or all RUC values. Results saved to: %s", outfile)
        else:
            logger.info("Request finished successfully. Results saved to: %s", outfile)

    return all_data

if __name__ == '__main__':
    main()