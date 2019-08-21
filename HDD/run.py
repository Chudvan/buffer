import os
import sys
import time


TIME_SLEEP = 5 * 60
DELETE_UNTIL = 2592000


def check_args():
    if len(sys.argv) != 1:
        raise TypeError("""Error: Too many arguments.
            Usage: python run.py""")


def parse_disk_list():
    list_disks = os.popen('fdisk -l | grep Disk\ /').read()
    if not list_disks:
        print('Warning: empty list_disks.')
        print('Continue? (y/n)')
        answer = input()[0]
        if answer != 'y':
            sys.exit(-1)
    return [string.split()[-1] for string in list_disks.split(':')[:-1]]


def run_smartctl(list_disks, TIME_SLEEP):
    result_disks = []
    for disk in list_disks:
        result = int(os.popen('smartctl -a /dev/sda | grep "# 1" | tr -s " " | cut -f9 -d" "').read())
        os.popen('smartctl -t short "{}"'.format(disk))
        time.sleep(TIME_SLEEP)
        result -= int(os.popen('smartctl -a /dev/sda | grep "# 1" | tr -s " " | cut -f9 -d" "').read())
        if bool(result):
            result_disks.append(disk)
    return result_disks


def delete_entries(DELETE_UNTIL):
    os.system('python "{}" "{}"'.format('delete_entry.py', time.time() - DELETE_UNTIL))


def new_tests(result_disks):
    for disk in result_disks:
        os.system('python "{}" "{}"'.format('HDD.py', disk))


check_args()
list_disks = parse_disk_list()
result_disks = run_smartctl(list_disks, TIME_SLEEP)
delete_entries(DELETE_UNTIL)
new_tests(result_disks)
