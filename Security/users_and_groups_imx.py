import paramiko, argparse, sys
import re, pprint, collections,time

parser = argparse.ArgumentParser(description="Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)
parser.add_argument('-a', '--action', help='get/put/cmd', dest="action", required=True)
parser.add_argument('-w', '--pathTCUfile', help='path to the TCU file', dest="tcu_file")
parser.add_argument('-x', '--pathToYourFile', help='Needed only for put usecases', dest="your_file")
parser.add_argument('-c', '--command', help='Need only for command execute cases', dest="command")

args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key
action = args.action
command = str(args.command)
tcu_file = args.tcu_file
your_file = args.your_file

dictionary_uid = dict()

def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client

def action_to_perform(action):
    global out
    if action == "cmd":
        check_udif()
    else:
        print("Your action: {} is invalid".format(action))
        sys.exit(11)

def call_cmd(cmd1):
    ssh = createSSHClient(server, port, user, key)
    (stdin, stdout, stderr) = ssh.exec_command(cmd1)
    out = stdout.read().decode('ISO-8859-1')
    stdin.close()
    stdout.close()
    stderr.close()
    ssh.close()
    if out:
        # print(out.replace("â", ""))  # only for case "systemctl --failed"
        return out
    else:
        # print(stderr.read().decode('ISO-8859-1'))
        return out

def check_udif():
    global dictionary_uid
    out = call_cmd(command)
    pid_lists = []
    name_lists = []
    for x in out.splitlines():
        l = re.search(r"(^\d+)\s.*\s(/.*)", x.lstrip(" "))
        pid_lists.append(l.group(1))
        name_lists.append(l.group(2))
    dictionary = dict(zip(pid_lists, name_lists))

    for key, value in dictionary.items():
        uid = call_cmd("cat /proc/{}/status | grep -oE 'Uid:\s*[0-9]*'".format(key))
        uid_nr = re.search(r"\d+$", uid.strip())
        dictionary_uid[value] = uid_nr.group(0)

def getKeysByValue(dictOfElements, valueToFind):
    listOfKeys = list()
    listOfItems = dictOfElements.items()
    for item  in listOfItems:
        if item[1] == valueToFind:
            listOfKeys.append(item[0])
    return  listOfKeys

def remove_whitelist(dictionar,user_defined_whitelist):
    temporary_list = []
    white_list1 = []
    for x in user_defined_whitelist:
        try:
            white_list1.append(call_cmd(f"cat /etc/passwd | cut -d: -f1,3 | grep -E {x}").split(':')[1].strip())
        except Exception as e:
            print(f"User: {x}, was not found! Exception occured as '{e}'")
    for i in white_list1:
        for key in dictionar:
            if dictionar[key] == i:
                temporary_list.append(key)
    for x in temporary_list:
        del dictionar[x]
    return dictionar

def checking_user_uniqueness():
    global dictionary_uid
    dictionary_uid = remove_whitelist(dictionary_uid,user_defined_whitelist)
    duplicates =[item for item, count in collections.Counter(dictionary_uid.values()).items() if count > 1]
    pprint.pprint(duplicates)
    if len(duplicates) > 0:
        print("==========================================================================================\n")
        for x in duplicates:
                print("Users which started more application/processes: \n")
                print(call_cmd("cat /etc/passwd | cut -d: -f1,3 | grep -E ':{}$'".format(x)))
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
        app = re.search(r"(.*):", call_cmd("cat /etc/passwd | cut -d: -f1,3 | grep -E ':{}$'".format(x)))
        users.append(app.group(1))
    for x in users:
        c = 0
        f_l = []
        groups = call_cmd("cat /etc/group | grep {}".format(x)).splitlines()
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

def checking_restrict_uid():
    pass

if __name__ == "__main__":
    start_time = time.time()
    user_defined_whitelist = ["pd_swl_dc_omadm", "radio", "system","pd_dlt","pd_iptables-ctrl","root","modem"]  # user will insert here the whitelisted users , user root will be treated in another TC
    ssh = createSSHClient(server, port, user, key)
    action_to_perform(action)
    check_udif()
    checking_user_uniqueness()
    checking_groups()
    print("\n====================================END===================================================\n")
    end_time = time.time()
    print(f"Successfully parsed in {str(end_time - start_time)[0:4]} seconds !")
