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
    #get the total services by number and name
    ceva = device.shell(
        "ps | grep -v 'grep' | grep -v '/bin/sh' | grep -E '/opt/conti-drt' | tr -s ' '").splitlines()
    numar_servicii = []
    nume_servicii = []

    for x in ceva:
        l = re.search(r"(\d+)\s+.*conti-drt.bin.(\w+.*)", x.lstrip(" "))
        numar_servicii.append(l.group(1))
        nume_servicii.append(l.group(2))

    print("Please check bellow if the processes are respecting the Umask Rule:")
    print("\n")
    for index,each in enumerate(numar_servicii):
        # do a cat for every service found above
        output = device.shell(f"cat /proc/{numar_servicii[index]}/status | grep -i umask".format(each))
        if "Umask" and "0007" in output:
            print(f"Following process: {each} {nume_servicii[index]} has the correct Umask:")
        else:
            print(f"Following process: {each} {nume_servicii[index]} does not have the correct Umask:")

        # for x in output.splitlines():
        #     each = r"{}".format(each)
        #     fi = re.search(r"^\/lib\/systemd\/system\/([a-zA-Z\-]+)\.service\:ExecStart={}".format(each), x)
        #     if fi:
        #         services_list.append(fi.group(1))
        #         break
#
#
# def checking_service():
#     # negative testing
#     for x in services_list:
#         out = device.shell("cat /lib/systemd/system/{}.service".format(x))
#         if "User=" in out or "Group=" in out:
#             print("ERROR: found a deviation from the rule for {}".format(x))
#
#
# def checking_sericesd():
#     # positive testing
#     l = []
#     for x in services_list:
#         out = device.shell("cat /lib/systemd/system/{}.service.d/access.conf".format(x))
#         if "User=" in out and "Group=" in out:
#             print("Everything is set correctly for {} ".format(x))
#             l.append(x)
#     diff = [item for item in services_list if item not in l]
#     print("Deviation from rules : {}".format(diff))
#
# def checking_umask():
#     print("\n CHECKING THE UMASK\n")
#     for x in services_list:
#         out = device.shell("cat /lib/systemd/system/{}.service.d/access.conf".format(x))
#         if "UMask=" in out:
#             umask = out[out.find("UMask="):].strip()
#             print("Service {} have {}".format(x, umask))
#             if umask.endswith("7"):
#                 print("UMask is correctly set")
#             else:
#                 print("ERROR: UMask is not correctly set")



if __name__ == "__main__":
    refresh_device('adb kill-server', 'adb devices')
    create_connection()
    extracting_services()
    # checking_service()
    # checking_sericesd()
    # checking_umask()
