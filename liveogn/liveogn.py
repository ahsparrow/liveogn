import gevent
from random import uniform
import requests
import sqlite3
import time
import xml.etree.ElementTree as ET

LIVEOGN_URL = "http://live.glidernet.org/lxml.php"

def get_liveogn():
    result = {}

    # Query data from live OGN
    params = {'a': 0,
              'b': 59.0, 'c': 50.0, 'd': 2.0, 'e': -6.0,
              'z': 1}
    try:
        r = requests.get(LIVEOGN_URL, params=params)
    except requests.RequestException:
        print("Request exception")
        return result

    # Parse XML
    try:
        root = ET.fromstring(r.text)
    except ET.ParseError:
        print("ElementTree parse error")
        return result

    # Get list of aircraft
    for element in root.findall('m'):
        str = element.attrib.get('a')
        if str:
            vals = str.split(',')
            if len(vals) > 12:
                id = vals[12]
                if id != "0":
                    try:
                        result[id] = {
                            'lat': float(vals[0]),
                            'lon': float(vals[1]),
                            'reg': vals[2],
                            'alt': int(vals[4]),
                            'tim': vals[5]}
                    except ValueError:
                        print("Value error")
            else:
                print("Not enough values")
        else:
            print("No attribute")

    return result

def init_db(db_file):
    conn = sqlite3.connect(db_file)
    with conn as c:
        c.execute("""create table fixes
                     (id text primary key, lat real, lon real, alt integer, reg text, tim text)""")

def reset_db(db_file):
    conn = sqlite3.connect(db_file)
    with conn as c:
        c.execute("delete from fixes")

def update_db(db_file):
    fixes = get_liveogn()

    conn = sqlite3.connect(db_file)
    with conn as c:
        for id, fix in fixes.items():
            c.execute("insert or replace into fixes (id, reg, lat, lon, alt, tim) values (?, ?, ?, ?, ?, ?)",
                      (id,
                       fix['reg'],
                       float(fix['lat']),
                       float(fix['lon']),
                       int(fix['alt']),
                       fix['tim']))

def liveogn_task(db_file):
    while 1:
        local = time.localtime()

        if local.tm_hour == 9 and local.tm_min > 50:
            reset_db(db_file)
        elif local.tm_hour >= 10 and local.tm_hour <= 19:
            update_db(db_file)

        # Update every five minutes
        secs = time.time()
        delta = 300 - (secs % 300) + uniform(1, 10)
        gevent.sleep(delta)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("db_file", help="Database file")
    parser.add_argument("--init", action="store_true", help="Initialise database")
    args = parser.parse_args()

    if args.init:
        init_db(args.db_file)

    g = gevent.spawn(liveogn_task, args.db_file)
    gevent.joinall([g])


