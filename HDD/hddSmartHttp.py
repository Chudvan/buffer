# -*- encoding: utf-8 -*-
import BaseHTTPServer
import xml.etree.cElementTree as xml
import sqlite3
import datetime
import traceback

ENCODING = 'utf-8'
NAME_DB = '/home/ufo/.UFO/var/hddsmart.sqlite3'
LOG_NAME = 'log.txt'
FILENAME_ANSWER = 'new.xml'
SEP_LONG = 30


class XML:
    @staticmethod
    def parse_request(request):
        bad_request_code = 400
        good_request_code = 200
        try:
            request_element = xml.fromstring(request)
        except xml.ParseError:
            return bad_request_code, 'Error: XML declaration not well-formed.'
        check_results = []
        data_attrib = request_element.attrib
        check_results.append(data_attrib)
        elements_dict = {element.tag: element for element in request_element}
        tags = ['Count', 'HddTest']
        for tag in tags:
            if tag not in elements_dict:
                return bad_request_code, 'Error: Expected element: {}.'.format(tag)
        try:
            count = tags[0]
            count_val = int(elements_dict[count].text)
            if count_val <= 0:
                return bad_request_code, "Error: Expected element Count > 0."
            check_results.append(count_val)
        except ValueError:
            return bad_request_code, "Error: Expected int element: <Count></Count>."
        try:
            hdd_test = tags[1]
            atrib_dict = elements_dict[hdd_test].attrib
            atrib_list = [('ctrl', 'READ'), ('code', int), ('tms', int)]
            ctrl = atrib_list[0][0]
            ctrl_val = atrib_list[0][1]
            if atrib_dict[ctrl] != ctrl_val:
                raise KeyError
        except KeyError:
            return bad_request_code, "Error: Expected attribute: ctrl='READ'."
        try:
            code = atrib_list[1][0]
            code_type = atrib_list[1][1]
            if code in atrib_dict:
                uniq_id = code_type(atrib_dict[code])
                check_results.append((code, uniq_id))
                return good_request_code, check_results
        except ValueError:
            return bad_request_code, "Error: Expected int attribute: code."
        try:
            tms = atrib_list[2][0]
            tms_type = atrib_list[2][1]
            if tms in atrib_dict:
                tms_val = atrib_dict[tms]
                if len(tms_val) != 10:
                    raise ValueError
                unix_time = tms_type(tms_val)
                if unix_time < 0:
                    raise ValueError
                check_results.append((tms, unix_time))
                return good_request_code, check_results
        except ValueError:
            return bad_request_code, "Error: Expected int attribute: tms in format DDDDDDDDDD"
        return bad_request_code, "Error: Expected one of attributes: code or tms."

    @staticmethod
    def create_answer(test_entries, attributes_entries, data_attrib):
        data = xml.Element('data')
        data_attrib.update({'type': 'REPLY'})
        data.attrib = data_attrib
        i = 0
        test_columns = ['hddModule', 'testStatus', 'hddFilling', 'hddSysFilling', 'hddName', 'hddSerial']
        attr_columns = ['name', 'value', 'thresh', 'type', 'raw_value']
        for test in test_entries:
            hdd_test = xml.Element('HddTest')
            code = test[0]
            hdd_test.attrib = {'tstamp': test[1],
                               'code': unicode(code)}
            for n in range(len(test_columns)):
                sub_element = xml.SubElement(hdd_test, test_columns[n])
                sub_element.text = unicode(test[n + 2])
            for attr in attributes_entries[i:]:
                test_id = attr[1]
                if test_id == code:
                    hdd_attribute = xml.SubElement(hdd_test, 'hddAttributes')
                    hdd_attribute.attrib = {'code': unicode(attr[0])}
                    for n in range(len(attr_columns)):
                        sub_element = xml.SubElement(hdd_attribute, attr_columns[n])
                        sub_element.text = unicode(attr[n + 2])
                    i += 1
                else:
                    break
            data.append(hdd_test)
        tree = xml.ElementTree(data)
        return tree


class Database(object):
    def __init__(self, name_database):
        self.name_database = name_database
        self.connection = sqlite3.connect(name_database)
        self.cursor = self.connection.cursor()

    def get_tms(self, unix_time, count):
        sql_query = """SELECT min(uniqID)
        FROM test
        WHERE unixtime >= strftime('%s', {}, 'unixepoch')""".format(unix_time)
        self.cursor.execute(sql_query)
        code = self.cursor.fetchall()[0][0]
        if code is None:
            return 404, 'Warning: entries later than {} unixtime are not found.'.format(unix_time)
        return self.get_code(code, count)

    def get_code(self, code, count):
        sql_query = "SELECT * FROM test WHERE {} <= uniqID and uniqID < {}.".format(code, code + count)
        try:
            self.cursor.execute(sql_query)
            test_entries = self.cursor.fetchall()
            if not test_entries:
                return 404, 'Warning: entries with uniqID more than {} are not found.'.format(code)
            from_to = (test_entries[0][0], test_entries[-1][0])
            sql_query = """SELECT *
            FROM attributes
            WHERE {} <= testID and testID <= {}""".format(from_to[0], from_to[1])
            self.cursor.execute(sql_query)
            attributes_entries = self.cursor.fetchall()
            return 200, test_entries, attributes_entries
        except sqlite3.OperationalError:
            answer = "Error: can't make a request '{}'.".format(sql_query)
            for name_database in ['test', 'attributes']:
                sql_query = """SELECT name FROM sqlite_master WHERE type='table' AND name='{}'.""".format(name_database)
                self.cursor.execute(sql_query)
                if not self.cursor.fetchall():
                    return 500, answer + '\n' + 'Error: table {} is not exist.'.format(name_database)
            return 500, answer


class MyHTTPServer(BaseHTTPServer.HTTPServer):
    pass


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def basic_answer(self, code, text_answer, text_logging=''):
        if not text_logging:
            text_logging = text_answer
        self.send_response(code)
        self.send_header("Content-length", len(text_answer))
        self.end_headers()
        self.wfile.write(text_answer)
        self.wfile.close()
        self.logging('Status code: {}\nAnswer: {}'.format(code, text_logging))
        self.logging('-' * SEP_LONG)

    @staticmethod
    def logging(text):
        with open(LOG_NAME, 'a') as f:
            f.write(text + '\n')

    @staticmethod
    def get_time():
        return datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    def setup(self):
        now = self.get_time()
        self.logging('Date Time: {}'.format(now))
        self.logging('Request from: {}.'.format(self.client_address))
        return BaseHTTPServer.BaseHTTPRequestHandler.setup(self)

    def do_POST(self):
        try:
            content_type = self.headers.gettype()
            if content_type != 'text/xml':
                status_code = 400
                answer = 'Error: Expected content-type: text/xml'
                self.basic_answer(status_code, answer)
                return
            content_length = int(self.headers.get('Content-length'))
            request = self.rfile.read(content_length)
            self.logging('Client request:\n{}.'.format(request))
            parse_results = XML.parse_request(request)
            status_parse = parse_results[0]
            if status_parse != 200:
                answer = parse_results[1]
                self.basic_answer(status_parse, answer)
                return

            db = Database(NAME_DB)
            count = parse_results[1][1]
            db_request_type = parse_results[1][2][0]
            if db_request_type == 'code':
                code = parse_results[1][2][1]
                db_result = db.get_code(code, count)
            elif db_request_type == 'tms':
                tms = parse_results[1][2][1]
                db_result = db.get_tms(tms, count)
            else:
                status_code = 500
                answer = 'Error: Inform your provider about this problem.'
                self.basic_answer(status_code, answer)
                return
            status_db = db_result[0]
            if status_db != 200:
                answer = db_result[1]
                self.basic_answer(status_db, answer)
                return
            test_entries, attributes_entries = db_result[1:]
            data_attrib = parse_results[1][0]
            tree = XML.create_answer(test_entries, attributes_entries, data_attrib)
            with open(FILENAME_ANSWER, 'w') as f:
                tree.write(f, encoding=ENCODING)
            with open(FILENAME_ANSWER, 'r') as f:
                answer = f.read()
            status_code = 200
            self.basic_answer(status_code, answer, 'Correct answer.')
        except:
            exception_text = traceback.format_exc()
            RequestHandler.logging('Error: Exception happened.\n' + exception_text)


if __name__ == '__main__':
    now = RequestHandler.get_time()
    RequestHandler.logging('Start serving {}.'.format(now))
    RequestHandler.logging('-' * SEP_LONG)
    server = MyHTTPServer(('', 8009), RequestHandler)
    server.serve_forever()
