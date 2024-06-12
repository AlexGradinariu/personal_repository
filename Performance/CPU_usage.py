import paramiko
import argparse
import re
'''
Test scenario : command busctl to check all services that are using dbus connections.
For those services perform a systemctl cat 'service'
Check the result, ex : BusName=com.contiautomotive.ramses.diagnosismanager
Check in /etc/dbus-1/system.d for the config file that contains above busname , via grep -r 'busname' location
if no dbus name, manually check the xml files before baseline creation
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
#function that will return any given command
def ssh_command(cmd):
    ssh = createSSHClient(server, port, user, key)
    (stdin, stdout, stderr) = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    stdin.close()
    stdout.close()
    stderr.close()
    ssh.close()
    if out:
        return out
    else:
        return out

def get_processes_running(white_listed):
    sum_of_all_cpu =[]
    processes = []
    usages = []
    regex = '(\d+)%\s+(\d+)%\s(.*)'
    list_of_processes = ssh_command(f"top n -1")
    for line in list_of_processes.splitlines():
        match = re.search(regex, line)
        if match is not None:
            processes.append(match.group(2))
            usages.append(match.group(3))
    zipped_list = list(zip(processes, usages))
    # Remove whitelisted items from the zipped list
    zipped_list = [(p, u) for (p, u) in zipped_list if not any(w in u for w in white_listed)]
    # Separate the remaining processes and usages
    processes, usages = zip(*zipped_list)
    # Print the remaining processes and usages
    for process, usage in zip(processes, usages):
        print(f"{process}%: {usage}")
        sum_of_all_cpu.append(int(process))
    if (sum(sum_of_all_cpu)) <= 80:
        print(f"CPU usage is {sum(sum_of_all_cpu)}%, under 80% limit !")
    else:
        print(f"CPU usage is {sum(sum_of_all_cpu)}%, over 80% limit !")


if __name__ == '__main__':
    white_list = ["dlt-system", "dlt-daemon", "logmanager", "memory_statistics", "auditd", "clear_logs", "tcpdump",
               "subsystem_ramdump", "agetty", "getty", "sh", "do_nad_ramdump", "sshd", "mbecall", "servicecall",
               "smm.exe", "xdelta_ua", "swl_ru_", "swl_ua_","bin/busybox"]
    get_processes_running(white_list)
