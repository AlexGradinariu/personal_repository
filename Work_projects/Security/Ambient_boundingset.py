import lxml.doctestcompare
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
    AmbientCapabilities = []
    CapabilityBoundingSet = []
    services_started_by_opt_applications = []

    # Extract into a list every services that runs under conti-drt.
    drt_applications = device.shell("egrep -ri 'ExecStart=.*/opt/conti-drt/bin/' /lib/systemd/system").splitlines()
    for x in drt_applications:
        regex = "(.*)/(.*):ExecStart"
        l = re.search(regex, x.lstrip(" "))
        try:
            services_started_by_opt_applications.append(l.group(2))
        except:
            pass

      #Extract a list with "AmbientCapabilities" of every process under systemd_services
    systemd_ambientcapabilities = device.shell("grep -ri 'AmbientCapabilities' /lib/systemd/system | grep -v 'grep'").splitlines()
    for x in systemd_ambientcapabilities:
        regex = "(.*)\/(.*):Ambient"
        l = re.search(regex, x.lstrip(" "))
        try:
            AmbientCapabilities.append(l.group(2))
        except:
            pass

    # Extract a list with "CapabilityBoundingSet" of every process under systemd_services
    systemd_CapabilityBoundingSet = device.shell("grep -ri 'CapabilityBoundingSet' /lib/systemd/system | grep -v 'grep'").splitlines()
    for x in systemd_CapabilityBoundingSet:
        regex = "(.*)\/(.*):Capability"
        l = re.search(regex, x.lstrip(" "))
        try:
            CapabilityBoundingSet.append(l.group(2))
        except:
            pass

    #Check if any opt service is using systemd feature AmbientCapabilities:
    for x in services_started_by_opt_applications:
        if x in AmbientCapabilities:
            print(f"The following service '{x}' is using AmbientCapabilities from /lib/systemd/system")

    # Check if any opt service is using systemd feature CapabilityBoundingSet:
    for x in services_started_by_opt_applications:
        if x in CapabilityBoundingSet:
            print(f"The following service '{x}' is using CapabilityBoundingSet from /lib/systemd/system")

if __name__ == "__main__":
    lista_drepturi = []
    refresh_device('adb kill-server', 'adb devices')
    create_connection()
    get_the_access_rights()
    print("\n====================================END===================================================\n")