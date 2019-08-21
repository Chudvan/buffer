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
    list_disks = os.popen('fdisk -l | grep \ /dev/').read()
    if not list_disks:
        print('Warning: empty list_disks.')
        print('Continue? (y/n)')
        answer = input()[0]
        if answer != 'y':
            sys.exit(-1)
    return [string.split()[-1] for string in list_disks.split(':')[:-1]]


def get_life_time(hdd):
    return int(os.popen('smartctl -a "{}" | grep "# 1" \
    | tr -s " " | cut -f9 -d" "'.format(hdd)).read())


def run_smartctl(list_disks, TIME_SLEEP):
    for hdd in list_disks:
        cur_life_time = get_life_time(hdd)
        start_time = time.time()
        os.popen('smartctl -t short "{}"'.format(hdd))
        while cur_life_time == get_life_time(hdd) and (time.time() - start_time) <= TIME_SLEEP:
            time.sleep(5)


def delete_entries(DELETE_UNTIL):
    os.system('python "{}" "{}"'.format('delete_entry.py', time.time() - DELETE_UNTIL))


def new_tests(list_disks):
    for disk in list_disks:
        os.system('python "{}" "{}"'.format('HDD.py', disk))


check_args()
list_disks = parse_disk_list()
run_smartctl(list_disks, TIME_SLEEP)
delete_entries(DELETE_UNTIL)
new_tests(list_disks)
