# -*- encoding: utf-8 -*-
import os
import sys
import sqlite3
import time


class Database(object):
    def __init__(self, name_database):
        self.name_database = name_database
        self.connection = sqlite3.connect(name_database)
        self.cursor = self.connection.cursor()
        sql_query = """CREATE TABLE IF NOT EXISTS test(
                    uniqID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    unixtime TEXT NOT NULL,
                    hddModule TEXT NOT NULL,
                    testStatus TEXT NOT NULL,
                    hddFilling TEXT NOT NULL,
                    hddName TEXT NOT NULL,
                    hddSerial TEXT NOT NULL
                    )"""
        self.cursor.execute(sql_query)
        sql_query = """CREATE TABLE IF NOT EXISTS attributes(
                    uniqID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    testID INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    value INTEGER NOT NULL,
                    thresh TEXT NOT NULL,
                    type TEXT NOT NULL,
                    raw_value TEXT NOT NULL
                    )"""
        self.cursor.execute(sql_query)

    def put_in_database(self, table, data_list):
        sql_query = """INSERT INTO {} """.format(table)
        if table == 'test':
            sql_query += """(unixtime, hddModule, testStatus, hddFilling, hddName, hddSerial)
                         VALUES (?, ?, ?, ?, ?, ?)"""
        elif table == 'attributes':
            sql_query += """(testID, name, value, thresh, type, raw_value)
                         VALUES (?, ?, ?, ?, ?, ?)"""
        else:
            raise Exception("Error: Incorrect Table Name")
        self.cursor.executemany(sql_query, data_list)
        self.connection.commit()

    def get_lastID(self, table):
        if table != 'test' and table != 'attributes':
            raise Exception("Error: Incorrect Table Name")
        sql_query = """SELECT MAX(uniqID) FROM {}""".format(table)
        self.cursor.execute(sql_query)
        return self.cursor.fetchall()[0][0]


class Parser(object):
    @staticmethod
    def parse_hdd_test(hdd):
        unix_time = int(time.time())
        hdd_module = os.popen('smartctl -a "{}" | grep Device\ Model | tr -s " " | cut -f3,4 -d " "'.format(hdd)).read()
        if not hdd_module:
            print('Warning: hdd_module is empty.')
        status = os.popen('smartctl -a "{}" | grep "# 1" | tr -s " " | cut -f6,7 -d " "'.format(hdd)).read()
        if not status:
            print('Trying to run short test...')
            print(os.popen('smartctl -t short "{}" | sed -n "/Testing/,/Please/p"'.format(hdd)).read())
            time.sleep(120)
            status = os.popen('smartctl -a "{}" | grep "# 1" | tr -s " " | cut -f6,7 -d " "'.format(hdd)).read()
        if status == 'read failure\n':
            status = u'Не пройдена'
        elif status == 'without error\n':
            status = u'Пройдена'
        else:
            print("Warning: Can't parse hdd test result.")
        percent = os.popen('df -h / | grep /dev | cut -c 54-57').read()[:-1]
        if not percent:
            print("Warning: percent is empty.")
        hdd_serial = os.popen('smartctl -a "{}" | grep Serial\ Number'.format(hdd)).read()
        if not hdd_serial:
            print('Warning: hdd_serial is empty.')
        else:
            hdd_serial = hdd_serial.split()[-1]
        return unix_time, hdd_module, status, percent, hdd, hdd_serial

    @staticmethod
    def parse_hdd_attributes(database, hdd):
        command_text = os.popen('smartctl -a "{}" | sed -n "/RAW_VALUE/,/Error Log/p"'.format(hdd)).read()
        if not command_text:
            raise OSError("Error: Can't parse SMART attributes.")
        data_list = []
        lastID = database.get_lastID('test')
        for line in command_text.split('\n')[1:-3]:
            cur_list = line.split()
            data_list.append(
                (lastID,
                 cur_list[1],
                 int(cur_list[3]),
                 cur_list[5],
                 cur_list[6],
                 cur_list[9])
            )
        return data_list


def is_device(hdd):
    check_str = os.popen('file {}'.format(hdd)).read()
    check = False
    for hdd_type in ['character special', 'block special']:
        if hdd_type in check_str:
            check = True
            break
    return check


if len(sys.argv) == 2:
    name_db = 'database.db'
    '''
    if not os.path.splitext(sys.argv[1])[1] == '.db':
        raise TypeError("""name_database must ends with '.db'""")
    '''
    db = Database(name_db)
    hdd_name = sys.argv[1]
    if not is_device(hdd_name):
        raise TypeError("""Device is not exists or it's not character special/block special""")
    test_data = [Parser.parse_hdd_test(hdd_name)]
    db.put_in_database('test', test_data)
    attributes_data = Parser.parse_hdd_attributes(db, hdd_name)
    db.put_in_database('attributes', attributes_data)
elif len(sys.argv) <= 2:
    raise TypeError("""Not enough arguments.
        Usage: python script.py hdd_name""")
else:
    raise TypeError("""Error: Too many arguments.
    Usage: python script.py hdd_name""")
