# -*- encoding: utf-8 -*-
import sys
import sqlite3
import datetime


class Database(object):
    def __init__(self, name_database):
        self.name_database = name_database
        self.connection = sqlite3.connect(name_database)
        self.cursor = self.connection.cursor()

    def delete_until(self, unix_time):
        for table in ['test', 'attributes']:
            sql_query = """SELECT name FROM sqlite_master WHERE type='table' AND name='{}'""".format(table)
            self.cursor.execute(sql_query)
            if not len(self.cursor.fetchall()):
                raise IOError("Error: '{}' table is not exist.".format(table))
        sql_query_1 = """SELECT uniqID 
                    FROM test WHERE unixtime < strftime('%s', '{}', 'unixepoch')
                    """.format(unix_time)
        sql_query_2 = """DELETE FROM {}
                      WHERE testID IN ({})
                      """.format('attributes', sql_query_1)
        sql_query_3 = """DELETE FROM {}
                    WHERE uniqID IN ({})
                    """.format('test', sql_query_1)
        sql_queries = [sql_query_1, sql_query_2, sql_query_3]
        try:
            sql_query = None
            for sql_query in sql_queries:
                self.cursor.execute(sql_query)
                self.connection.commit()
        except sqlite3.OperationalError:
            raise sqlite3.OperationalError("Error: can't make a request '{}'.".format(sql_query))


def is_unix_time(unix_time):
    check = False
    try:
        u_time = float(unix_time)
        if u_time < 0:
            return False
        datetime.datetime.fromtimestamp(u_time)
    except (ValueError, TypeError, OSError):
        return check
    else:
        check = True
        return check


if len(sys.argv) == 2:
    name_db = 'database.db'
    db = Database(name_db)
    unix_time = sys.argv[1]
    if not is_unix_time(unix_time):
        raise ValueError("""Error: Incorrect unixtime format.
        Select number of seconds from 01.01.1970. 
        Example: 1565964649.0689025""")
    db.delete_until(unix_time)
elif len(sys.argv) <= 2:
    raise TypeError("""Error: Not enough arguments.
    Usage: python delete_entry.py unix_time""")
else:
    raise TypeError("""Error: Too many arguments.
    Usage: python delete_entry.py unix_time""")
