from ppadb.client import Client
from subprocess import Popen, PIPE, STDOUT
import re, time, os, pprint, collections


def refresh_device(kill, check):
   counter = 0
   flag = 0
   while counter <= 2:
        if flag:
           break
        p = Popen(kill, stdout=PIPE, stderr=STDOUT)
        if not p.stderr:
            p1= Popen(check, stdout=PIPE, stderr=STDOUT)
            for line in p1.stdout:
                line = str(line).lstrip("b'").rstrip(".\\n'\\r")
                expected = re.search(r"^\w*\\tdevice$", line)
                if expected:
                    a = expected.group(0).replace("\\t", " ")
                    if "device" in a:
                        print(a)
                        flag = 1
                        break
                    else:
                        counter += 1
                        time.sleep(10)
   else:
        print("device is not connected")
        quit()

def create_connection():
    global device
    adb = Client(host='127.0.0.1', port=5037)
    devices = adb.devices()
    device = devices[0]

def get_the_uid():
    global dictionary_uid
    ceva = device.shell("ps | grep -v ]$ | grep -v grep | grep -v ps | grep -E '/usr/bin|/opt/conti-drt' | tr -s ' '").splitlines()
    pid_lists = []
    name_lists = []
    for x in ceva:
        l = re.search(r"(^\d+)\s.*\s(/.*)", x.lstrip(" "))
        pid_lists.append(l.group(1))
        name_lists.append(l.group(2))
    dictionary = dict(zip(pid_lists, name_lists))
    pprint.pprint(dictionary)
    dictionary_uid = {}
    for key, value  in dictionary.items():
        uid = device.shell("cat /proc/{}/status | egrep -o 'Uid:\s*[0-9]*'".format(key))
        uid_nr = re.search(r"\d+$", uid.strip())
        dictionary_uid[value] = uid_nr.group(0)

def getKeysByValue(dictOfElements, valueToFind):
    listOfKeys = list()
    listOfItems = dictOfElements.items()
    for item  in listOfItems:
        if item[1] == valueToFind:
            listOfKeys.append(item[0])
    return  listOfKeys

def checking_user_uniqueness():
    duplicates =[item for item, count in collections.Counter(dictionary_uid.values()).items() if count > 1]
    if len(duplicates) > 0:
        print("==========================================================================================\n")
        for x in duplicates:
                print("Users which started more application/processes: \n")
                print(device.shell("cat /etc/passwd | cut -d: -f1,3 | grep -E ':{}$'".format(x)))
                list_c = getKeysByValue(dictionary_uid, x)
                print("Bellow you can find the processes which are running on the user: \n")
                print(list_c)
                print("\n==========================================================================================")


def checking_groups():
    uids = set()
    users = list()
    for key, value in dictionary_uid.items():
        uids.add(value)
    for x in uids:
        app = re.search(r"(.*):", device.shell("cat /etc/passwd | cut -d: -f1,3 | grep -E ':{}$'".format(x)))
        users.append(app.group(1))
    for x in users:
        c = 0
        f_l = []
        groups = device.shell("cat /etc/group | grep {}".format(x)).splitlines()
        c = len(groups)
        for y in groups:
            group = re.search(r"(.*):(x|\*)", y)
            f_l.append(group.group(1))
            c -= 1
            if c == 0:
                for z in f_l:
                    if x != "root" and z == "root":
                        print("ERROR: User {} is making part of a sensitive group(root, pers-admin, net_raw, otp). Below you can found the groups: \n{}) ".format(x, f_l))
                        print('\n')
                    elif x != "root" and z == "pers-admin":
                        print("ERROR: User {} is making part of a sensitive group(root, pers-admin, net_raw, otp). Below you can found the groups: \n{}) ".format(x, f_l))
                        print('\n')
                    elif x != "root" and z == "otp":
                        print("ERROR: User {} is making part of a sensitive group(root, pers-admin, net_raw, otp). Below you can found the groups: \n{}) ".format(x, f_l))
                        print('\n')
                    elif x != "root" and z == "net_raw":
                        print("ERROR: User {} is making part of a sensitive group(root, pers-admin, net_raw, otp). Below you can found the groups: \n{}) ".format(x, f_l))
                        print('\n')

def checking_restrict_uid():
    pass

if __name__ == "__main__":
    refresh_device('adb kill-server', 'adb devices')
    create_connection()
    get_the_uid()
    checking_user_uniqueness()
    checking_groups()
    print("\n====================================END===================================================\n")

















