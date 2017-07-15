#!/usr/bin/env python3
import consulta
import sys
import os
import csv
import itertools


def main(args=None):
    if args is None:
        args = sys.argv

    if len(args) != 3:
        print("Incorrect number of arguments")
        return
    if not os.path.isfile(args[1]):
        print("Input file does not exist")
        return

    ruc_list = []
    with open(args[1], 'r') as input_file:
        ruc_list = list(set(ruc.strip() for ruc in input_file if ruc.strip()))

    data = consulta.main(['--ruc'] + ruc_list)
    with open(args[2], 'w') as out_file:
        writer = csv.writer(out_file)
        writer.writerow([
            "Nombre", "RUC", "CIIU", "Descripción", "Revision"
        ])
        for ruc in data:
            columns = [ruc['nombre'], ruc['ruc']]
            for index, ciiu in enumerate(get_main_ciiu(ruc['ciiu'])):
                cod_ciiu = str(ciiu.codigo)
                cod_ciiu = cod_ciiu + '\\' if cod_ciiu.startswith('0') else cod_ciiu

                columns.extend([
                    cod_ciiu,
                    ciiu.descripcion,
                    str(ciiu.revision)
                ])
            writer.writerow(columns)


def get_main_ciiu(ciiu_list):
    per_revision = []
    for k, v in itertools.groupby(ciiu_list, lambda x: x.revision):
        per_revision.append(list(v))

    main_per_revision = map(lambda x: x[0], per_revision)
    return main_per_revision


if __name__ == '__main__':
    main()
