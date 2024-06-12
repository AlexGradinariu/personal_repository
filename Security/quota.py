import argparse, serial, time, re

parser = argparse.ArgumentParser(description= "Checking for quotas")
parser.add_argument('-p', '--port', help='SoC port', dest="port", required=True)
parser.add_argument("-t",'--time', help='timeout time', dest="timee", required=True)
parser.add_argument("-tcu", '--tcu_hw', help='signed/secured', dest="type", required=True)
args = parser.parse_args()
port = args.port
timee = args.timee
type = args.type


def conv_KB_to_GB(input_kilobyte):
    gigabyte = 1.0 / 1000000
    convert_gb = gigabyte * input_kilobyte
    return convert_gb

def conv_MB_to_GB(input_megabyte):
    gigabyte = 1.0 / 1024
    convert_gb = gigabyte * input_megabyte
    return convert_gb

def getSerialOrNone(port):
    try:
        ser = serial.Serial(port= port)
        return True
    except:
       return False

def listen_port(port,timee):
    global l
    l = []
    if getSerialOrNone(port):
        serBarCode = serial.Serial(port=port, baudrate=115200,timeout=0,rtscts=0,xonxoff=0)
        timeout = time.time() + int(timee)
        timeout_start = time.time()
        while True and time.time() < timeout:
            BarCode = serBarCode.readline()
            if len(BarCode) >= 3:
                s = BarCode.decode("utf-8").strip("\r\n")
                l.append(s)
                print(s)
        serBarCode.close()
    else:
        print("Port is not usable")

def extract_user_and_totalvalue(l):
    global users, totalvalue
    users = []
    for x in l:
        if re.search(r"#\d+",x):
            tmp = re.search(r"#\d+\s*--\s*\d+\w\s*\d+\w\s*(\d+\w)",x)
            users.append(tmp.group(1))
        elif re.search(r"\/dev\/mmcblk0\s*(\d+\.\d)+G",x):
            totalvalue = re.search(r"\/dev\/mmcblk0\s*(\d+\.\d)+G",x).group(1)


if __name__ == "__main__":
    l = []
    listen_port(port, timee)
    extract_user_and_totalvalue(l)
    l.clear()
    for element in users:
        if element.endswith("K"):
            element = int(element.rstrip("K"))
            element = conv_KB_to_GB(element)
            l.append(element)
        elif element.endswith("M"):
            element = int(element.rstrip("M"))
            element = conv_MB_to_GB(element)
            l.append(element)
    if type == "SECURED":
        if sum(l) <= float(totalvalue):
            print(sum(l))
            print("All quotas was not exceeded the space of emmc")
        else:
            print("Quotas exceeded the emmc space")
    elif type == "SIGNED":
        if sum(l) - 0.7 <= float(totalvalue):
            print(sum(l))
            print("All quotas was not exceeded the space of emmc")
        else:
            print("Quotas exceeded the emmc space")

