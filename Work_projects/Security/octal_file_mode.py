from ppadb.client import Client
from subprocess import Popen, PIPE, STDOUT
import re, time


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


def get_the_access_rights():
    owner = []
    group = []
    others = []
    octal_rights = device.shell("ls -lR  /opt/conti-drt ; ls -lR  /data | grep pd").splitlines()
    for x in octal_rights:
        l = re.search(r"(.*)\s\s\s\s\d\s(\w+).*(:\d\d)\s(.*)", x.lstrip(" "))
        try:
            a = l.group(1)
            b = l.group(4)
            owner.append((a[1:4],b))
            group.append((a[4:7],b))
            others.append((a[7:10],b))
        except:
            pass

    print("\n'OTHER' unwanted execution rights for each file under '/opt/conti-drt or /data | grep pd':\n")
    for x in others:
        if "x" in x[0]:
            print(f"File -> {x[1]} <- has unwanted others execution rights as '{x[0]}'!")
        elif "r" in x[0]:
            print(f"File -> {x[1]} <- has unwanted others read rights as '{x[0]}'!")
        elif "w" in x[0]:
            print(f"File -> {x[1]} <- has unwanted others write rights as '{x[0]}'!")

    print("\n=======================================================================================\n")

    print("\n'Write flag' for owner,group and others for each file under '/opt/conti-drt or /data | grep pd':\n")
    for x in owner:
        if "w" in x[0]:
            print(f"File -> {x[1]} <- has unwanted write rights for owner as '{x[0]}'!")
    for x in group:
        if "w" in x[0]:
            print(f"File -> {x[1]} <- has unwanted write rights for group as '{x[0]}'!")

if __name__ == "__main__":
    lista_drepturi = []
    refresh_device('adb kill-server', 'adb devices')
    create_connection()
    get_the_access_rights()
    print("\n====================================END===================================================\n")