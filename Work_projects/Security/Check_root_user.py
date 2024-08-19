import paramiko, argparse,time

parser = argparse.ArgumentParser(description="Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)
parser.add_argument('-c', '--command', help='Need only for command in test cases execution', dest="command")
args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key
command = str(args.command)

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

def check_services_as_root(ls_command):
    unit_files = ssh_command(ls_command).strip()
    services_with_root = []
    for x in unit_files.splitlines():
        try:
            a = ssh_command(f"systemctl show -pUser {x}").strip().split("=")[1]
            services_with_root.append(x) if len(a) == 0 or a == 'root' else print(f"Service: {x:<35s} has user: {a:<30s} {'looks ok'}! ",flush=True)
        except : pass

    print("==========================================================================================\n")
    print("Checking services with issues:")
    for x in services_with_root:
        try:
            a = ssh_command(f"systemctl show -pUser {x}").strip().split("=")[1]
            # a = a if a else 'blank'
            print(f"Service: {x:<50s} has user: {'blank' if len(a) == 0  else a:<30s} {'does not look ok'}! ",flush=True)
        except : pass

    if len(services_with_root) == 0:
        print("==========================================================================================\n")
        print("Everything looks ok !")
    else:
        print("==========================================================================================\n")
        print(f"{len(services_with_root)} Issues found during service check !")

if __name__ == "__main__":
    ssh = createSSHClient(server, port, user, key)
    start_time = time.time()
    print("\n============================Check services for root owner======================================\n")
    check_services_as_root(command)
    print("\n====================================END===================================================\n")
    end_time = time.time()
    print(f"Successfully parsed in {str(end_time - start_time)[0:4]} seconds !")