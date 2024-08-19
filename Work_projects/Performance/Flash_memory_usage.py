import paramiko
import re, argparse



'''Intra partition utilisation:
        A. check req. : df -h /data <= 80%
        B. check req. : df -h /data/persistency <= 80%
        Intra-UBI utilization:
        C. check req. : (ubinfo /dev/ubi0 -N dsp2) / max.dsp2 <= 80%
        D. check req. : (ubinfo /dev/ubi0 -N system) / max.system <= 80%
        E. E - SW growth consistency check
        (ubinfo /dev/ubi0 -N uarea + ubinfo /dev/ubi0 -N test) / 2 > ((max.dsp2 + max.system) - (ubinfo /dev/ubi0 -N dsp2 + ubinfo /dev/ubi0 -N system))
        F. F - combined intra-UBI for DSP2 and System
        (ubinfo /dev/ubi0 -N dsp2 + ubinfo /dev/ubi0 -N system) / (max.system + max.dsp2) <= 80%

        if C or D fails:
            - if F is ok, set failed out of C or D to warning only
            - if F is nok, set failed out of C or D to error (and F failed / error)'''



parser = argparse.ArgumentParser(description= "Insert values specific to type of TCU - High / Entry")
parser.add_argument('-S', '--system_max_size', help='SYSTEM_max_size', dest="system_size", required=True)
parser.add_argument('-D', '--DSP2_max_size', help='Your request', dest="dsp2_size", required=True)
parser.add_argument('-i', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)

args=parser.parse_args()
system_size = int(args.system_size)
dsp2_size = int(args.dsp2_size)
server = args.ip
port = int(args.port)
user = args.user
key = args.key
SYSTEM_max_size = system_size
DSP2_max_size = dsp2_size


def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client


def Intra_partition_utilisation():
# A. check req. : df -h /data <= 80%
# B.check req.: df - h / data / persistency <= 80 %
    nume_filesystem = []
    percentage = []
    reg_exp = "ubi0:(\w+).*\s(\w+)%"
    ssh = createSSHClient(server, port, user, key)
    (stdin, stdout, stderr) = ssh.exec_command("df -h /data && df -h /data/persistency")
    ceva = stdout.read().decode('ISO-8859-1').splitlines()
    for x in ceva:
        l = re.search(reg_exp,x.lstrip(" "))
        if l != None:
            nume_filesystem.append(l.group(1))
            percentage.append(float(l.group(2)))
    for x in percentage :
        var = percentage.index(x)
        y = nume_filesystem[var]
        if x < 80:
            print(f"A.B.Check for intra-partition is fullfilled, Filesystem '{y}' is using {x}% of allocated memory.")
        else:
            print(f"A.B.Check for intra-partition is NOT fullfiled, Filesystem '{y}' is using {x}% of allocated memory.")

def Intra_UBI_utilisation(entry_DSP2_max_size,entry_SYSTEM_max_size):
#C. check req. : (ubinfo /dev/ubi0 -N dsp2) / max.dsp2 <= 80%
#D. check req. : (ubinfo /dev/ubi0 -N system) / max.system <= 80%
    f_flag = False
    cd_flag = False
    name = []
    size = []
    size_regex = "\s(\d+.\d+)\sMiB"
    name_regex = "Name:\s+(\w+)"
    ssh = createSSHClient(server, port, user, key)
    (stdin, stdout, stderr) = ssh.exec_command("ubinfo /dev/ubi0 -N uarea && ubinfo /dev/ubi0 -N test && ubinfo /dev/ubi0 -N dsp2 && ubinfo /dev/ubi0 -N system")
    ceva = stdout.read().decode('ISO-8859-1').splitlines()
    for x in ceva:
        l = re.search(size_regex, x.lstrip(" "))
        s = re.search(name_regex, x.lstrip(" "))
        if l != None:
            size.append(float(l.group(1)))
        if s != None:
            name.append(s.group(1))

#Calculate the percentage of occupied dsp2 filesystem:
    DSP2_filesystem_percentage = size[2] / entry_DSP2_max_size * 100
    System_filesystem_percentage = size[3] / entry_SYSTEM_max_size * 100
    if DSP2_filesystem_percentage < 80 and System_filesystem_percentage < 80:
        print(f"C.D.Intra-UBI utilization for DSP2 and System is OK, DSP2 Filesystem using {round(DSP2_filesystem_percentage,2)}% and System using {round(System_filesystem_percentage,2)}% of allocated memory.")
    else:
        print(f"C.D.Intra-UBI utilization for DSP2 and System is NOK, DSP2 Filesystem using {round(DSP2_filesystem_percentage, 2)}% and System using {round(System_filesystem_percentage, 2)}% of allocated memory.")
        cd_flag = True

#E. (ubinfo /dev/ubi0 -N uarea + ubinfo /dev/ubi0 -N test) / 2 > ((max.dsp2 + max.system) - (ubinfo /dev/ubi0 -N dsp2 + ubinfo /dev/ubi0 -N system))
    #Calculus
    urea_test=(size[0]+size[1])/2
    maxdsp_maxsystem=(entry_SYSTEM_max_size+entry_DSP2_max_size) - (size[2]+size[3])
    if urea_test > maxdsp_maxsystem:
        print(f"E.SW growth consystency Check passed {round(urea_test,2)} MB > {round(maxdsp_maxsystem,2)} MB.")
    else:
        print(f"E.SW growth consystency Check NOT Passed {round(urea_test,2)} MB > {round(maxdsp_maxsystem,2)} MB.")

#F. (ubinfo /dev/ubi0 -N dsp2 + ubinfo /dev/ubi0 -N system) / (max.system + max.dsp2) <= 80%
    check =(size[2]+size[3])/(entry_SYSTEM_max_size+entry_DSP2_max_size)*100
    if check < 80:
        print(f"F.Check for Combined Intra-UBI utilisation of both DSP2 and System is OK, total usage space of System + DSP2 filesystem is {round(check,2)}% of allocated memory")
    else:
        print(f"F.Check for Combined Intra-UBI utilisation of both DSP2 and System is NOK, total usage space of System + DSP2 filesystem is {round(check, 2)}% of allocated memory")
        f_flag = True

    if cd_flag == True and f_flag == True:
        print("Checking of Partition Flash space usage is with status Failed!")
    elif cd_flag == True and f_flag == False:
        print("Checking of Partition Flash space usage is with status Warning!")
    print(f"Item size used for calculations are {size[0]}MB for {name[0]}, {size[1]}MB for {name[1]}, {size[2]}MB for {name[2]}, {size[3]}MB for {name[3]}, with maximum allocated size for System {system_size}MB and for DSP2 {dsp2_size}MB .")


if __name__ == "__main__":
    Intra_partition_utilisation()
    Intra_UBI_utilisation(DSP2_max_size,SYSTEM_max_size)