import os
import csv
from io import StringIO
from dateutil.parser import parse
import json

PH_TABLE_SUPERBLOCK = "POINTHISTORY"
DEFAULT_PATH = 'gh-pages'

def write_helper(file_name, data):
    with open(os.path.join(DEFAULT_PATH, file_name), 'w') as fp:
        json.dump(data, fp)


def get_PH_table(path):
    fp_ph = StringIO()

    table_find = False
    with open(path) as fp:
        for line in fp:
            if table_find:
                fp_ph.write(line)

            elif line.strip() == "POINTHISTORY":
                table_find = True

    fp_ph.seek(0)

    return fp_ph


def process_PH(fp):
    records = []
    fieldnames = ["N_UN", 'point', 'item', 'N_CNT', 'NN', 'N_ADM', 'date', 'user']
    reader = csv.DictReader(fp, fieldnames=fieldnames)

    for row in reader:
        if row['N_CNT'] == '0':
            if not row['item'].startswith(("衰减", "Decay")):
                continue
            else:
                row['item'] = "衰减"
        # insert record
        row['type'] = row['N_CNT']      # 1: item, 0: Decay
        for key in ["N_UN", "NN", 'N_CNT', "N_ADM"]:
            del row[key]

        row['point'] = round(float(row['point']) * -1, 2)

        records.append(dict(row))

    fp.close()

    return records


def build_tables(dkp_reocrds, date_since='2020-02-12 09:00:00'):
    user_table = []
    avg_dkp_table = []
    loot_table = []

    tmp_dkp_table = {}

    date_since = parse(date_since) if date_since is not None else None

    for record in dkp_reocrds:
        if date_since is not None:
            r_date = parse(record['date'])
            if r_date < date_since:
                continue

        loot_table.append(record)
        if record['user'] not in user_table:
            user_table.append(record['user'])

        if record['item'] == "衰减":
            continue

        if record['item'] not in tmp_dkp_table:
            tmp_dkp_table[record['item']] = []

        tmp_item_dkp = {'user': record['user'], 'point': record['point'], 'date': record['date']}
        tmp_dkp_table[record['item']].append(tmp_item_dkp)

    for item_name in tmp_dkp_table:
        avg_dc = {"item": item_name, "min": 0, "max": 0, "count": 0, "avg": 0}
        records = tmp_dkp_table[item_name]
        avg_dc['his'] = records

        avg_dc['count'] = len(records)

        tmp_list = [x['point'] for x in records]
        avg_dc['max'] = max(tmp_list)
        avg_dc['min'] = min(tmp_list)
        avg_dc['avg'] = round(sum(tmp_list) / avg_dc['count'], 2)

        avg_dkp_table.append(avg_dc)

    write_helper("user_table.json", user_table)
    write_helper("avg_dkp_table.json", avg_dkp_table)
    write_helper("dkp_reocrds.json", loot_table)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('./prog file')
        exit()

    t = get_PH_table(sys.argv[1])
    ph = process_PH(t)
    build_tables(ph)