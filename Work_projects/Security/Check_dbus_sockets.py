import paramiko
import argparse

'''
Path Checkings:
Using "netstat -x"  command we can see any path that is using a dbus socket.
The purpose of the tests is to check if those paths have their own resonable users id, and not using root.
Check also uids for tcp6 and upd6 by cat /proc/net/tcp6 | udp6 and aftewards cat /etc/passwd | grep proc, 
and check if the process is not root started.
Alex G.
'''

parser = argparse.ArgumentParser(description= "Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)


args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key

#create ssh client
def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client

def ssh_command(cmd):
    (stdin, stdout, stderr) = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    if out:
        return out
    else:
        return out

def get_nestat_info():
    #Populate a list with all available paths after using netstat -x command, in order to check if they use dbus sockes
    Services = ssh_command("netstat -x | egrep CONNECTED | grep -v system | grep -v /var/run/charon.vici |awk '{print$8}'")
    for x in Services.splitlines():
        if len(x) != 0:
            path_list.append(x)

def check_path_owner():
    #Check if from above output if there are path which are using "Root" as owner !
    index = 0
    for x in path_list:
        owner = ssh_command(f"ls -la {x}" + " | awk '{print$3,$4}'")
        if "root" in owner:
            index += 1
            print(f"The following path '{x}' has owner as root!")
    if index != 0:
        print(f"{index} Issues found, there are paths which are using 'root' as owner, this is not allowed ! Please check !")
    else:
        print("No issues found for checking path owner !")

def check_uid_info_tcp6():
    #create a list with all uids from /proc/net/tcp6
    uid_tcp6 = ssh_command("cat /proc/net/tcp6 | grep -v 'when' |awk '{print$8}'")
    for x in uid_tcp6.splitlines():
        if x != "0":
            uid_list_tcp6.append(x)

def check_uid_owner_tcp6():
    #check for each uid from tcp6 that is not using root as name owner
    index = 0
    for x in uid_list_tcp6:
        owner = ssh_command(f"cat /etc/passwd | grep {x}")
        if owner.startswith("root"):
            index += 1
            print(f"Following uid '{x}' has owner as root, as follows \n{owner}!")
    if index != 0:
        print(f"{index} Issues found, there are uids which are using 'root' as owner, this is not allowed ! Please check !")
    else:
        print("No issues found for checking TCP6 UIDs !")

def check_uid_info_udp6():
    #create a list with all uids from /proc/net/udp6
    uid_udp6 = ssh_command("cat /proc/net/udp6 | grep -v 'when' |awk '{print$8}'")
    for x in uid_udp6.splitlines():
        if x != "0":
            uid_list_udp6.append(x)

def check_uid_owner_udp6():
    #check for each uid from udp that is not using root as name owner
    index = 0
    for x in uid_list_udp6:
        owner = ssh_command(f"cat /etc/passwd | grep {x}")
        if owner.startswith("root"):
            index += 1
            print(f"Following uid '{x}' has owner as root, as follows \n{owner}!")
    if index != 0:
        print(f"{index} Issues found, there are uids which are using 'root' as owner, this is not allowed ! Please check !")
    else:
        print("No issues found for checking UDP6 UIDs !")

if __name__ == "__main__":
    ssh = createSSHClient(server, port, user, key)
    path_list = []
    uid_list_tcp6 = []
    uid_list_udp6 = []
    get_nestat_info()
    check_path_owner()
    check_uid_info_tcp6()
    check_uid_owner_tcp6()
    check_uid_info_udp6()
    check_uid_owner_udp6()
    print("Script finished !")