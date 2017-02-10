#!/usr/bin/env python3
import sys
from selenium import webdriver
import contextlib
import logging
import logging.config
import argparse
import json
import os

sys.path.append("..")
from ConsultaSunat.sunat import Sunat, InvalidRUCError
from ConsultaSunat.utils import CustomJSONEncoder


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
        help='Limit number of retries. Default: try until successful'
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

        for index, ruc in enumerate(ruc_list):
            logger.info("Started request for RUC: %d (%d/%d)", ruc, index + 1, len(ruc_list))
            retry = True
            num_retries = 0
            # If max_retries is not specified, the query is repeated until it succeeds
            while retry and (max_retries == -1 or num_retries < max_retries):
                num_retries += 1
                try:
                    data = sunat.get_all_information(ruc)
                except InvalidRUCError as e:
                    logger.error(e)
                    data = None
                    retry = False

                if data:
                    all_data.append(data)
                    retry = False

            if num_retries >= max_retries and max_retries != -1 and retry:
                logger.error("Max number of retries reached. Request for RUC: %d failed", ruc)
            elif not retry and not data:
                logger.error("Request for RUC: %d failed", ruc)
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
