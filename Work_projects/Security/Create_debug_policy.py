import os,argparse
import subprocess
import shutil,paramiko
import sys
import re,time
from scp import SCPClient

'''
Author: Alex G. SyI Team
Script created for automating the debug policy creation for IMX and NAD Nooes,as follow:
At the location of IMX_DebugPolicy folder, script will append new serial number at location 00_input\TCU_Serial_Numbers.txt
Creation process will Start for SAM File.
After creating SAM File, a new folder with the naming of the serial number will be created, SAM file will be moved there and afterwads will start the NAD debug policy creation.
Output from 98_tmp\nad_serial_number.txt will be used to create the NAD policy on a Linux Machine, with docker container installed there.
Start Docker environemnt in detached mode.
Give different commands specific to file creation.
Please fill in all the bellow arguments.
'''

parser = argparse.ArgumentParser(description= "Parsing some numbers")
parser.add_argument('-l', '--imx', help='Location of IMX_Debug_policy_folder', dest="imx", required=True)
parser.add_argument('-p', '--usr_password', help='usr_password for user', dest="usr_password", required=True)
parser.add_argument('-u', '--user', help='user , to be included with cw01', dest="user", required=True)
parser.add_argument('-s', '--server', help='Linux Machine were NAD debug policy toolchian exists', dest="server", required=True)
parser.add_argument('-t', '--uidn', help='Test user for Linux Machine were NAD debug policy toolchian exists', dest="uidn", required=True)
parser.add_argument('-x', '--tpass', help='Password for Linux Machine were NAD debug policy toolchian exists', dest="tuser", required=True)


args = parser.parse_args()
imx_dbgplc_folder = str(args.imx)
usr_password = str(args.usr_password)
user = str(args.user) # must be used mandatory as "cw01\uic81314" ,one \only
server = str(args.server)
linux_user = str(args.uidn)
test_user_password = str(args.tuser)


lista_seriale = []

def insert_IMX_serial(location_of_imx8_tool):
    while True:
        serial_number= input("Please inser serial number,press ENTER afterwards type 'END': ").upper()
        print(serial_number)
        if len(serial_number) == 20:
            lista_seriale.append(serial_number.upper())
            print(f"Serial number: {serial_number} added !")
        elif serial_number == "END":
            break
        elif len(serial_number) != 20:
            print("Lenght of serial number looks incorrect !")
            continue
    with open(os.path.join(location_of_imx8_tool,"00_input\TCU_Serial_Numbers.txt"), "w") as file:
        for x in lista_seriale:
            file.write(x)
    return lista_seriale

def create_imx_samfile(location_of_imx8_tool):
    # `path` is a variable that contains the path to the directory where the script is located.
    os.chdir(location_of_imx8_tool)
    command = "python 10_script\OTC_SAM_Signed+.py" + " " + f"-u {user}" + " " + f"-p {usr_password}" + " " + "-in 00_input/TCU_Serial_Numbers.txt"
    try:
        proces_comand = subprocess.Popen(command,shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Creating SAM file started,wait...",flush=True)
        out,err = proces_comand.communicate()
        if "SUCCESS : SAM-file created" in out.decode("utf-8"):
            print("SUCCESS : SAM-file created",flush=True)
        elif err:
            print(err.decode("utf-8"),flush=True)
            raise Exception("Issues during creating SAM file, script will stop here...")
    except Exception as e:
        print(f"Exception occured as {e} !")
        sys.exit(1)

def create_folder_and_cp_imx_samfile(location_of_imx8_tool):
    sam_folder_name = os.path.join(os.path.dirname(location_of_imx8_tool),lista_seriale[0])
    try:
        os.mkdir(sam_folder_name)
    except FileExistsError as e:
        print(e)
        print(f"Folder {lista_seriale[0]} already existing,script will stop here...!")
        sys.exit(1)
    try :
        shutil.copy(os.path.join(location_of_imx8_tool,"01_output\samimage.bin"),sam_folder_name)
        print(f"Sam file copied to folder {sam_folder_name}")
    except Exception as e :
        print(f"Exception occured as {e} !")

def fetch_nad_temp_serial_number(location_of_imx8_tool):
    try:
        with open(os.path.join(location_of_imx8_tool,"98_tmp","nad_serial_number.txt"), "r") as file:
            serial_nad = file.read().strip()
            print(f"NAD serial number for debug policy is : {serial_nad if len(serial_nad) != 0 else 'blank'} ")
            if len(serial_nad) == 0:
                raise Exception("NAD Serial number not available !")
    except Exception as e:
        print(e)
        print("Only SAM File created,will not proceed with NAD !")
        sys.exit(1)
    return serial_nad


def createSSHClient():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=server, username=linux_user, password=test_user_password)
    return client

def copy_sdx_file_locally(location_of_imx8_tool):
    '''Copy from Linux machine the sdx file to be edited with new Serial number '''
    high_sdx_file = "Downloads/NAD_Debug_Policy_Tool/Downloads/secbootcfg/debugpolicy/sdx55_debugpolicy.xml"
    entry_sdx_file = "Downloads/NAD_Debug_Policy_Tool/Downloads/secbootcfg/debugpolicy/sdx24_debugpolicy.xml"
    ssh = createSSHClient()
    '''Make a difference between HIGH and ENTRY, by checking the serial number apended in above list os serial'''
    if lista_seriale[0][4] == "E":
        with SCPClient(ssh.get_transport()) as scp:
            try:
                scp.get(entry_sdx_file, os.path.dirname(location_of_imx8_tool), recursive=True)
                print("Entry sdx files are succesfully copied locally !")
            except Exception as e:
                print(f"Exception occured as {e}!")
    else:
        with SCPClient(ssh.get_transport()) as scp:
            try:
                scp.get(high_sdx_file, os.path.dirname(location_of_imx8_tool), recursive=True)
                print("HIGH sdx files are succesfully copied locally !")
            except Exception as e:
                print(f"Exception occured as {e}!")
    ssh.close()

def modify_debug_policy_serial(new_serial,location_of_imx8_tool):
    print(f"Modifying debug policy with new serial number : {new_serial}")
    regex = re.compile(r"<serial_num>(.*)<\/serial_num>")
    try:
        with open(os.path.join(os.path.dirname(location_of_imx8_tool),("sdx24_debugpolicy.xml" if lista_seriale[0][4] == "E" else "sdx55_debugpolicy.xml")), "r") as file:
            lines = file.readlines()
            for line in lines:
                if re.search(regex, line):
                    index = lines.index(line)
                    line = re.sub(regex,f"<serial_num>{new_serial}</serial_num>", line)
                    lines[index] = line
        # write new replaced lines in file
        with open(os.path.join(os.path.dirname(location_of_imx8_tool),("sdx24_debugpolicy.xml" if lista_seriale[0][4] == "E" else "sdx55_debugpolicy.xml")), "w") as file1:
            for line in lines:
                file1.write(line)
        print("Entry debug policy was modified !" if lista_seriale[0][4] == "E" else "HIGH debug policy was modified !")
    except Exception as e :
        print(f"Exception occured as {e} !")
        sys.exit(1)

def copy_to_linuxmachine_modified_file(location_of_imx8_tool):
    '''Copy from local machine the edited sdx file back to the linux machine'''
    Remote_high_file = "Downloads/NAD_Debug_Policy_Tool/Downloads/secbootcfg/debugpolicy/sdx55_debugpolicy.xml"
    Remote_entry_file = "Downloads/NAD_Debug_Policy_Tool/Downloads/secbootcfg/debugpolicy/sdx24_debugpolicy.xml"
    local_file = os.path.join(os.path.dirname(location_of_imx8_tool),("sdx24_debugpolicy.xml" if lista_seriale[0][4] == "E" else "sdx55_debugpolicy.xml"))
    ssh = createSSHClient()
    '''Make a difference between HIGH and ENTRY, by checking the serial number apended in above list os serial'''
    if lista_seriale[0][4] == "E":
        with SCPClient(ssh.get_transport()) as scp:
            try:
                scp.put(local_file,Remote_entry_file, recursive=True)
                print("Your ENTRY files are succesfully copied to Linux Machine!")
            except Exception as e:
                print(f"Exception occured as {e}!")
                sys.exit(1)
    else:
        with SCPClient(ssh.get_transport()) as scp:
            try:
                scp.put(local_file, Remote_high_file, recursive=True)
                print("Your HIGH files are succesfully copied to Linux Machine!")
            except Exception as e:
                print(f"Exception occured as {e}!")
    ssh.close()

def create_NAD_debug_policy():
    ssh = createSSHClient()
    try:
        (stdin, stdout, stderr)  = ssh.exec_command("docker run -id --privileged --rm --name self-service-NAD --network host -v $HOME:$HOME -v /PROJ:/PROJ -v /etc/resolv.conf:/etc/resolv.conf -v /dev:/dev -v /sys/kernel/security:/sys/kernel/security vni-ce-devops-center-docker-l.artifactory.geo.conti.de/ubuntu_dev:18.04_drt15_prod /bin/bash")
        print(stdout.read().decode())
        print(stderr.read().decode())
        time.sleep(5)
        _,stdout,_ =ssh.exec_command("docker exec -i -u ${USER} --workdir /home/uidn1902/Downloads/NAD_Debug_Policy_Tool/Downloads self-service-NAD sudo pip install pyOpenSSL")
        print(stdout.read().decode())
        _, stdout, _ = ssh.exec_command("docker exec -i -u ${USER} --workdir /home/uidn1902/Downloads/NAD_Debug_Policy_Tool/Downloads self-service-NAD sudo pip install requests_toolbelt")
        print(stdout.read().decode())
        _, stdout, _ = ssh.exec_command("docker exec -i -u ${USER} --workdir /home/uidn1902/Downloads/NAD_Debug_Policy_Tool/Downloads self-service-NAD sudo chmod -R +x ./")
        print(stdout.read().decode())
        if lista_seriale[0][4] == "E":
            (stdin, stdout,stderr) = ssh.exec_command("docker exec -i -u ${USER} --workdir /home/uidn1902/Downloads/NAD_Debug_Policy_Tool/Downloads self-service-NAD" + " " + f"./secboot-sign-debugpolicy sa415m" + " " + user.split("\\")[0]+r"\\"+user.split("\\")[1] + " " + usr_password)
            print("Creating debug policy for ENTRY!")
            print(stdout.read().decode())
        else:
            (stdin, stdout, stderr) = ssh.exec_command("docker exec -i -u ${USER} --workdir /home/uidn1902/Downloads/NAD_Debug_Policy_Tool/Downloads self-service-NAD" + " " + f"./secboot-sign-debugpolicy sa515m" + " " + user.split("\\")[0]+r"\\"+user.split("\\")[1] + " " + usr_password)
            print("Creating debug policy for HIGH!")
            print(stdout.read().decode())
        (stdin, stdout, stderr) = ssh.exec_command("exit")
        print(stdout.read().decode())
        (stdin, stdout, stderr) = ssh.exec_command("docker stop self-service-NAD")
        print(stdout.read().decode())
        print("Docker container stopped successfully!")
        ssh.close()
    except Exception as e :
        print(f"Exception occured as {e} ! ")
        sys.exit(1)

def copy_debug_policy_file(location_of_imx8_tool):
    '''Copy debug policy from the Linux Machine '''
    high_sdx_file = "Downloads/NAD_Debug_Policy_Tool/Downloads/release_sdx55/"
    entry_sdx_file = "Downloads/NAD_Debug_Policy_Tool/Downloads/release_sdx24/"
    ssh = createSSHClient()
    '''Make a difference between HIGH and ENTRY, by checking the serial number apended in above list os serial'''
    if lista_seriale[0][4] == "E":
        with SCPClient(ssh.get_transport()) as scp:
            try:
                scp.get(entry_sdx_file, os.path.join(os.path.dirname(location_of_imx8_tool),lista_seriale[0]), recursive=True)
                print("Your ENTRY debug policies files are succesfully copied !")
            except Exception as e:
                print(f"Exception occured as {e}!")
    else:
        with SCPClient(ssh.get_transport()) as scp:
            try:
                scp.get(high_sdx_file, os.path.join(os.path.dirname(location_of_imx8_tool),lista_seriale[0]), recursive=True)
                print("Your HIGH debug policies files are succesfully copied !")
            except Exception as e:
                print(f"Exception occured as {e}!")
    ssh.close()

def create_debug_policy_archive(location_of_imx8_tool):
    if os.path.exists(os.path.join(os.path.dirname(location_of_imx8_tool),lista_seriale[0])):
        print(f"Creating archive for folder : {lista_seriale[0]} !")
        shutil.make_archive(os.path.join(os.path.dirname(location_of_imx8_tool),lista_seriale[0]),"zip",os.path.join(os.path.dirname(location_of_imx8_tool),lista_seriale[0]))
    else:
        print(f"Folder : {lista_seriale[0]} not existing,stopping here...")
        sys.exit(1)


if __name__ == "__main__":
    insert_IMX_serial(imx_dbgplc_folder)
    create_imx_samfile(imx_dbgplc_folder)
    create_folder_and_cp_imx_samfile(imx_dbgplc_folder)
    copy_sdx_file_locally(imx_dbgplc_folder)
    modify_debug_policy_serial(fetch_nad_temp_serial_number(imx_dbgplc_folder),imx_dbgplc_folder)
    copy_to_linuxmachine_modified_file(imx_dbgplc_folder)
    create_NAD_debug_policy()
    copy_debug_policy_file(imx_dbgplc_folder)
    create_debug_policy_archive(imx_dbgplc_folder)