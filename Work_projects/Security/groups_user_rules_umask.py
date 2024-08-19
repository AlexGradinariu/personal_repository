from ppadb.client import Client
from subprocess import Popen, PIPE, STDOUT
import re, time, os, pprint, collections
from ppadb.client import Client as AdbClient


def refresh_device(kill, check):
    counter = 0
    flag = 0
    while counter <= 2:
        if flag:
            break
        p = Popen(kill, stdout=PIPE, stderr=STDOUT)
        if not p.stderr:
            p1 = Popen(check, stdout=PIPE, stderr=STDOUT)
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


def extracting_services():
    global services_list
    ceva = device.shell(
        "ps | grep -v ]$ | grep -v grep | grep -v ps | grep -v '/bin/sh -$' | grep -v '{systemd} /sbin/init' | grep -v adbd | grep -E '/usr/bin|/opt/conti-drt' | tr -s ' '").splitlines()
    name_lists = []
    services_list = []
    for x in ceva:
        l = re.search(r"(^\d+)\s.*\s(/.*)", x.lstrip(" "))
        name_lists.append(l.group(2))
    for each in name_lists:
        output = device.shell("grep -s -r {} /lib/systemd/system".format(each))
        for x in output.splitlines():
            each = r"{}".format(each)
            fi = re.search(r"^\/lib\/systemd\/system\/([a-zA-Z\-]+)\.service\:ExecStart={}".format(each), x)
            if fi:
                services_list.append(fi.group(1))
                break


def checking_service():
    # negative testing
    for x in services_list:
        out = device.shell("cat /lib/systemd/system/{}.service".format(x))
        if "User=" in out or "Group=" in out:
            print("ERROR: found a deviation from the rule for {}".format(x))


def checking_sericesd():
    # positive testing
    l = []
    for x in services_list:
        out = device.shell("cat /lib/systemd/system/{}.service.d/access.conf".format(x))
        if "User=" in out and "Group=" in out:
            print("Everything is set correctly for {} ".format(x))
            l.append(x)
    diff = [item for item in services_list if item not in l]
    print("Deviation from rules : {}".format(diff))

def checking_umask():
    print("\n CHECKING THE UMASK\n")
    for x in services_list:
        out = device.shell("cat /lib/systemd/system/{}.service.d/access.conf".format(x))
        if "UMask=" in out:
            umask = out[out.find("UMask="):].strip()
            print("Service {} have {}".format(x, umask))
            if umask.endswith("7"):
                print("UMask is correctly set")
            else:
                print("ERROR: UMask is not correctly set")



if __name__ == "__main__":
    refresh_device('adb kill-server', 'adb devices')
    create_connection()
    extracting_services()
    checking_service()
    checking_sericesd()
    checking_umask()
