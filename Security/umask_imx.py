import paramiko, argparse, time

parser = argparse.ArgumentParser(description="Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)
parser.add_argument('-w', '--pathTCUfile', help='path to the TCU file', dest="tcu_file")
parser.add_argument('-x', '--pathToYourFile', help='Needed only for put usecases', dest="your_file")
parser.add_argument('-c', '--command', help='Need only for command execute cases', dest="command")

args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key
command = str(args.command)
tcu_file = args.tcu_file
your_file = args.your_file

def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client

def call_cmd(cmd1):
    (stdin, stdout, stderr) = ssh.exec_command(cmd1)
    out = stdout.read().decode('ISO-8859-1')
    if out:
        # print(out.replace("â", ""))  # only for case "systemctl --failed"
        return out
    else:
        # print(stderr.read().decode('ISO-8859-1'))
        return out

def check_udif():
        out = call_cmd(command)
        service_number = dict()
        # print(out)
        # print("")
        for x in out.splitlines():
            if "conti-drt/bin" in x:
                service_number.update({x.split()[0]: x.split()[4]})

        print("Please check bellow if the processes are respecting the Umask Rule:")
        print("\n")
        for key, value in service_number.items():
            # do a cat for every service found above
            output_t = call_cmd(f"cat /proc/{key}/status | grep -i umask")
            if "Umask" in output_t and "0007" in output_t:
                print(f"Following process: {key} {value} has the correct {output_t} ")
            else:
                print(f"Following process: {key} {value} does not have the correct {output_t.strip()} instead of 0007")

if __name__ == "__main__":
    ssh = createSSHClient(server, port, user, key)
    start_time = time.time()
    ssh = createSSHClient(server, port, user, key)
    check_udif()
    end_time = time.time()
    print(f"Successfully parsed in {str(end_time - start_time)[0:4]} seconds !")
