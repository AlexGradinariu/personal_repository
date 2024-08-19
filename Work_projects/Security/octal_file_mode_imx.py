import paramiko, argparse,time
import re

parser = argparse.ArgumentParser(description="Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)
parser.add_argument('-w', '--pathTCUfile', help='path to the TCU file', dest="tcu_file")
parser.add_argument('-x', '--pathToYourFile', help='Needed only for put usecases', dest="your_file")

args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key
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
    out = stdout.read().decode('utf-8')
    if out:
        return out
    else:
        return out

def check_octal_rights(path):
        out = call_cmd(f"ls -lR  {path}")
        owner = []
        group = []
        others = []
        for x in out.splitlines():
            l = re.search(r"(.*)\s\s\s\s\d\s(\w+).*(\d+)\s\w+\s\d+\s+\d+\s(.*)", x.lstrip(" "))
            try:
                a = l.group(1)
                b = path+'/'+l.group(4)
                owner.append((a[1:4], b))
                group.append((a[4:7], b))
                others.append((a[7:10], b))
            except:
                pass
        print(f"\n'OTHER' unwanted execution rights for each file under: \n")
        for x in others:
            if "x" in x[0]:
                print(f"File -> {x[1]:<40s} <- has unwanted others execution rights as : '{x[0]}'!")
            elif "r" in x[0]:
                print(f"File -> {x[1]:<40s} <- has unwanted others read rights as : '{x[0]}'!")
            elif "w" in x[0]:
                print(f"File -> {x[1]:<40s} <- has unwanted others write rights as : '{x[0]}'!")

        print("\n=======================================================================================\n")

        print(f"\n'Write flag' for owner,group and others for each file under:\n")
        for x in owner:
            if "w" in x[0]:
                print(f"File -> {x[1]:<40s} <- has unwanted write rights for owner as : '{x[0]}'!")
        for x in group:
            if "w" in x[0]:
                print(f"File -> {x[1]:<40s} <- has unwanted write rights for group as : '{x[0]}' !")

def check_octal_rights_system_objects():
    '''Function created to check all binary rights for bellow locations'''
    list_bin_paths = ["/bin/","/lib/","/lib/security/","/opt/conti/bin/","/opt/conti/lib/","/opt/conti-drt/bin/","/opt/conti-drt/lib/","/sbin/","/usr/bin/","/usr/lib/DRT/","/usr/lib/","/usr/sbin/"]
    list_bin_paths = ["/opt/conti/bin/","/opt/conti-drt/bin/"]
    list_bin_paths = set(list_bin_paths) # in order to remove any duplicates that may occur
    command_concatenate = "" #create te ls command for binary from the above list
    for x in list_bin_paths:
        # if x == list_bin_paths[-1]: unsued code
        #     a = f"ls -lR {x}"
        #     command_concatenate += a
        #     break
        # a = f"ls -lR {x}; "
        command_concatenate += x + " "
    out = call_cmd("ls -lR" + " " + command_concatenate + " | grep -E '\.sh|\.ko|\.so'")
    owner = []
    group = []
    others = []
    for x in out.splitlines():
        l = re.search(r"(.*)\s\s\s\s\d\s(\w+).*(:\d\d)\s(.*)", x.lstrip(" "))
        try:
            a = l.group(1)
            b = l.group(4)
            owner.append((a[1:4], b))
            group.append((a[4:7], b))
            others.append((a[7:10], b))
        except:
            pass

        for x in others: # check if all .ko,.so,.sh objects have write or execution rights.
            match_ko_so = re.search("\.ko|\.so",str(x[1])) # regex to search objects as : .ko, .so
            match_sh = re.search("\.sh",str(x[1])) # regex to search objects as : .sh
            if match_ko_so:
                if "x" in x[0]:
                    print(f"File -> {x[1]:<70s} {'<- has unwanted others execution rights as :':<50s} '{x[0]}'!")
                if "w" in x[0]:
                    print(f"File -> {x[1]:<70s} {'<- has unwanted others write rights as :':<50s} '{x[0]}'!")
            if match_sh:
                if "x" in x[0]:
                    print(f"File -> {x[1]:<70s} {'<- has unwanted others execution rights as :':<50s} '{x[0]}'!")
                if "w" in x[0]:
                    print(f"File -> {x[1]:<70s} {'<- has unwanted others write rights as :':<50s} '{x[0]}'!")
                if "r" in x[0]:
                    print(f"File -> {x[1]:<70s} {'<- has unwanted others read rights as :':<50s} '{x[0]}'!")



if __name__ == "__main__":
    start_time = time.time()
    ssh = createSSHClient(server, port, user, key)
    check_octal_rights('/opt/conti-drt/bin')
    # check_octal_rights_system_objects()
    end_time = time.time()
    print(f"Successfully parsed in {str(end_time - start_time)[0:4]} seconds !")
    print("\n====================================END===================================================\n")
