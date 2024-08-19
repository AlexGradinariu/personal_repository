import re, argparse, os, sys

parser = argparse.ArgumentParser(description= "Parsing for cyclic resets")
parser.add_argument('-l', '--port', help='Location of logs', dest="path", required=True)
parser.add_argument('-t', '--time', help='Location of logs', dest="t_final", required=True)
args = parser.parse_args()
path = args.path
t_final = float(args.t_final)

def parse_logs(path,node):
    kernel_time = []
    match = re.compile(f"\s(\d+\.\d+)\s\d+\s{node}")
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.startswith("messages"):
                with open(os.path.join(root, file), 'r', encoding="latin-1") as file:
                    for x in file.readlines():
                        a = match.search(x)
                        if a:
                            if float(a.group(1)) <= (t_final):#to acomodate some secodns from ATP delay between stoping the tracing and script
                                kernel_time.append(float(a.group(1)))
    kernel_time = sorted(kernel_time)
    # print(kernel_time)
    return(kernel_time[-1])

def in_range_values(float1,float2,range):
    return abs(float1 - float2) >= range

def check_for_resets(path,node):
    try:
        if in_range_values(parse_logs(path,node), t_final,20):
            print(f"Calculated Kernel uptime for {node} node is {parse_logs(path,node)} seconds  and calculated total up time in ATP is {t_final} seconds !")
            print(f"{node} was restarted")
        else:
            print(f"Calculated Kernel uptime for {node} node is {parse_logs(path, node)} seconds and calculated total up time in ATP is {t_final} seconds !")
            print(f"{node} node did not rebooted itself!")
    except Exception as e:
        print("Exception: " + str(e) + f" for {node} !")

def servicii_crapate(filename):
    reboot = re.compile("'reboot'.*(pid\s\w+).\sinvoked:|'poweroff'.*(pid\s\w+).\sinvoked:|'halt'.*(pid\s\w+).\sinvoked:")
    index = 0
    for root, dirs, files in os.walk(filename):
        for file in files:
            if file.startswith("messages"):
                with open(os.path.join(root, file), 'r', encoding="latin-1") as filer:
                    with open(os.path.join(path, "Failed_Services.txt"), 'a') as fw:
                        fw.write("\n")
                        fw.write("Fails are from following file {}: ".format(os.path.join(root, file)))
                        fw.write("\n")
                        for line in filer:
                            if "Unit entered failed state" in line:
                                index +=1
                                fw.write("Application crashdump situation       {}".format(line))
                                print("Unit entered failed state")
                            if reboot.search(line):
                                index += 1
                                fw.write("Application crashdump situation       {}".format(line))
                            if "error: Oops" in line:
                                index += 1
                                fw.write("Application crashdump situation       {}".format(line))
                                print("Kernel crash happened")
    if index != 0:
        print("Failed services and kernel issues present, check logs !")
    else:
        print("No Kernel issues found ! ")


if __name__ == "__main__":
    if not os.path.exists(path):
        print("Location is invalid!")
        sys.exit(0)
    print("Starting Check for NAD...")
    check_for_resets(path,"NAD")
    print("\n")
    print("Starting Check for IMX...")
    check_for_resets(path,"IMX")
    print("\n")
    print("Starting Check for kernel issues...")
    servicii_crapate(path)
    print("Script finished !")