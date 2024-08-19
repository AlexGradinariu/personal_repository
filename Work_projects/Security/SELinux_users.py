import paramiko, argparse,re

parser = argparse.ArgumentParser(description="Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)

args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key

def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client


def call_cmd(your_command):
    (stdin, stdout, stderr) = ssh.exec_command(your_command)
    out = stdout.read().decode('utf-8')
    if out:
        return out
    else:
        return out

def get_users_and_their_rights():
    regex = '(.*):x:'
    linux_users = []
    output = call_cmd('cat /etc/passwd')
    for line in output.splitlines():
        value = re.search(regex,line)
        if value:
            match = value.group(1)
            linux_users.append(match)
    print(f'System has a number of {len(linux_users)} users! ')
    for user in linux_users:
        print(f'Checking SELINUX Restriction for user: {user}')
        output = call_cmd(f"su - {user} -c 'systemctl status sshd.service' >/dev/null 2 && echo Success || echo Fail")
        if user == 'root' and 'Success' in output :
            print(f"User {user} has SELinux Restrictions setup : Correctly !")
            print('------')
        elif  user == 'factory' and 'Success' in output :
            print(f"User {user} has SELinux Restrictions setup : Correctly !")
            print('------')
        elif user != 'root' and 'Fail' in output :
            print(f"User {user} has SELinux Restrictions setup : Correctly !")
            print('------')
        else:
            print(f"User {user} has SELinux Restrictions setup : Incorrectly !")
            print(f"User {user} can access 'systemctl' commands !")
            print('------')

if __name__ == "__main__":
    ssh = createSSHClient(server, port, user, key)
    get_users_and_their_rights()
    ssh.close()
    print("Successfuly parsed ! ")