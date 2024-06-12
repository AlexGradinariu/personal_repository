import paramiko
import argparse
import pandas as pd
import re,os,sys
import time
from zipfile import ZipFile
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
parser.add_argument('-a', '--soc_location', help='SOC Files Location', dest="soc_location", required=True)
parser.add_argument('-d', '--destination', help='Destination of testfiles ', dest="destination", required=True)


args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key
soc_location = args.soc_location
destination = args.destination

#create ssh client
def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client
def ssh_command(cmd,client):
    (stdin, stdout, stderr) = client.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    if out:
        return out
    else:
        return out
def A7_NAND():
    client = createSSHClient(server, 23, user, key)
    result = ssh_command('df -h',client)
    list_with_all_other_values = []
    worst_case_static_value = 284.9
    # nad data regex
    ubi0test = 'ubi0:test\s+(.*)M\s+(.*)M.*tst'
    devloop0 = '\/loop0\s+(.*)M\s+(.*)M.*\/'
    ubidata0 = 'ubi0:data\s+\d+.\d+M\s+(.*)M\s(.*)M\s+(\d+)%\s.data'
    ubidatadsp2 = 'ubi0:dsp2\s+(.*)M\s+(.*)M.*'
    ubi0pers = 'ubi0:pers\s+\d+.\d+M\s+(.*)M\s(.*)M\s+(\d+)%\s.data'
    tmpfs = 'tmpfs\s+\d+.\d+M\s+(.*)[KMB]\s+(.*)M.*Principals'
    regex_nad = [ubi0test, devloop0, devloop0, ubidata0, ubidatadsp2, ubidatadsp2, ubi0pers, ubi0pers, tmpfs]
    memory_backup = 80
    available_nand = 1024
    for x in regex_nad:
        if x == tmpfs:
            try:
                used_values = re.search(x, result)
                match = used_values.group(1)
                if match:
                    list_with_all_other_values.append(float(match)/1024.0)
            except Exception as ex:
                print(ex)
                print(f"Regex failing to find something is {x}")
        else:
            try:
                used_values = re.search(x, result)
                match = used_values.group(1)
                if match:
                    list_with_all_other_values.append(float(match))
            except Exception as ex:
                print(ex)
                print(f"Regex failing to find something is {x}")
    used_nand = round(sum(list_with_all_other_values) + memory_backup + worst_case_static_value ,2)
    used_nand_percent = round((used_nand / available_nand) * 100,2)
    return available_nand,used_nand,used_nand_percent
def A35_eMMC():
    client = createSSHClient(server, 22, user, key)
    result = ssh_command('df -h',client)
    list_with_all_other_values = []
    bootfs = 42
    GPT_2 = 1
    backup = 44
    dmtable = 2
    fdb = 1
    available_emmc = 4557
    mapperrotfs = 'mapper.rootfs\s+.*M\s+(.*)[MGB]'
    data_dec = 'dev.data_dec\s+.*[MBG]\s+(.*)[MBG]\s+(.*)[MBG]'
    pers_dec = 'pers_dec\s+.*[MBG]\s+(.*)[MBGK]\s+(.*)[MBG]'
    sota_dec = 'dev.sota_dec\s+.*[MBG]\s+(.*)[MBGK]\s+(.*)[MBG]'
    regex_imx = [mapperrotfs, mapperrotfs, data_dec, pers_dec, pers_dec, sota_dec]
    for x in regex_imx:
        if x == pers_dec:
            try:
                used_values = re.search(x, result)
                match = used_values.group(1)
                if float(match) > 17:
                    list_with_all_other_values.append(float(match)/1024.0)
            except Exception as ex:
                print(ex)
                print(f"Regex failing to find something is {x}")
        elif x == sota_dec:
            try:
                used_values = re.search(x, result)
                match = used_values.group(1)
                if float(match) > 1.6:
                    list_with_all_other_values.append(float(match)/1024.0)
            except Exception as ex:
                print(ex)
                print(f"Regex failing to find something is {x}")
        else:
            try:
                used_values = re.search(x, result)
                match = used_values.group(1)
                if match:
                    list_with_all_other_values.append(float(match))
            except Exception as ex:
                print(ex)
                print(f"Regex failing to find something is {x}")
    static_values = 2*bootfs+2*GPT_2+backup+2*dmtable+fdb
    used_emmc = round(sum(list_with_all_other_values,static_values), 2)
    used_percent = round((used_emmc / available_emmc) * 100,2)
    return available_emmc,used_emmc,used_percent
def A35_NOR(directory, destination):
    NOR_allocated = 8
    file = [file for file in os.listdir(directory) if "uuu-flash-spinor-emmc" in file]
    for file in file:
        flash_spinor_emmc = os.path.join(directory,file)
        with ZipFile(flash_spinor_emmc, "r") as flash:
            flash.extractall(destination)
    #get file size
    spin_file = "flash_spinor_all.bin"
    spinor_size = round(os.path.getsize(os.path.join(directory,spin_file)) / (1024*1024),2)
    tswbin_size = round(os.path.getsize(os.path.join(destination,"tsw.bin")) / (1024*1024),2)
    occupied_NOR = spinor_size*2 + tswbin_size
    percentage_consumed = round((occupied_NOR / NOR_allocated) * 100,2)
    return NOR_allocated,occupied_NOR,percentage_consumed
def A7_RAM():
    Total_allocated = 1024
    v2x_static_allocated_quota = 50.7
    Total_consumed  = 0
    client = createSSHClient(server, 23, user, key)
    result = ssh_command('cat /proc/meminfo', client)
    regex = "MemFree:\s+(\d+)\skB"
    try:
        memory_used = re.search(regex,result)
        match = memory_used.group(1)
        if match:
            Total_consumed = round(Total_allocated - float(match)/1024,2)
    except Exception as ex:
        print(ex)
    if os.getenv("CV2X") == "YES-CV2X":
        print("China/V2X Version for RAM Consumtion")
        percentage_consumed = round((Total_consumed + v2x_static_allocated_quota) / Total_allocated * 100, 2)
        return Total_allocated, Total_consumed, percentage_consumed
    else:
        print("Europe Version for RAM Consumtion,without quota of 50.7 MB allocated")
        percentage_consumed =round((Total_consumed /Total_allocated)*100,2)
        return Total_allocated,Total_consumed,percentage_consumed
def A35_RAM():
    Total_allocated = 512
    Total_consumed = 0
    client = createSSHClient(server, 22, user, key)
    result = ssh_command('cat /proc/meminfo', client)
    regex = "MemFree:\s+(\d+)\skB"
    try:
        memory_used = re.search(regex,result)
        match = memory_used.group(1)
        if match:
            Total_consumed = round(Total_allocated - float(match)/1024,2)
    except Exception as ex:
        print(ex)
    percentage_consumed =round((Total_consumed/Total_allocated)*100,2)
    return Total_allocated,Total_consumed,percentage_consumed
def A35_eMMC_CHN():
    client = createSSHClient(server, 22, user, key)
    result = ssh_command('df -h',client)
    list_with_all_other_values = []
    V2x = 1740.8
    bootfs = 42
    GPT_2 = 1
    backup = 44
    dmtable = 2
    fdb = 1
    available_emmc = 4483
    mapperrotfs = 'mapper.rootfs\s+.*M\s+(.*)[MGB]'
    data_dec = 'dev.data_dec\s+.*[MBG]\s+(.*)[MBG]\s+(.*)[MBG]'
    pers_dec = 'dev.pers_dec\s+.*[MBG]\s+(.*)[MBGK]\s+(.*)[MBG]'
    sota_dec = 'dev.sota_dec\s+.*[MBG]\s+(.*)[MBGK]\s+(.*)[MBG]'
    regex_imx = [mapperrotfs, mapperrotfs, data_dec, pers_dec, pers_dec, sota_dec]
    for x in regex_imx:
        if x == pers_dec:
            try:
                used_values = re.search(x, result)
                match = used_values.group(1)
                if float(match) > 17:
                    list_with_all_other_values.append(float(match)/1024.0)
            except Exception as ex:
                print(ex)
                print(f"Regex failing to find something is {x}")
        elif x == sota_dec:
            try:
                used_values = re.search(x, result)
                match = used_values.group(1)
                if float(match) > 1.6:
                    list_with_all_other_values.append(float(match)/1024.0)
            except Exception as ex:
                print(ex)
                print(f"Regex failing to find something is {x}")
        else:
            try:
                used_values = re.search(x, result)
                match = used_values.group(1)
                if match:
                    list_with_all_other_values.append(float(match))
            except Exception as ex:
                print(ex)
                print(f"Regex failing to find something is {x}")

    static_values = 2*bootfs+2*GPT_2+backup+2*dmtable+fdb + V2x
    used_emmc = round(sum(list_with_all_other_values,static_values), 2)
    used_percent = round((used_emmc / available_emmc) * 100,2)
    return available_emmc,used_emmc,used_percent
def remove_test_files(folder):
    mmc_files = [files for files in os.listdir(folder) if files.startswith("mmc")]
    flash_files = [files for files in os.listdir(folder) if files.endswith(".bin")]
    uuu = 'uuu.auto'
    files_to_delete = []
    files_to_delete.extend(mmc_files)
    files_to_delete.extend(flash_files)
    files_to_delete.append(uuu)
    full_path_for_files = [os.path.join(folder,file) for file in files_to_delete]
    #delete actual files
    for file in full_path_for_files:
        os.remove(file)
        print("Removing file " + file)


if __name__ == '__main__':
    start = time.time()
    A7_total_NAND, consumed_nand, A7_NAND_percentage = A7_NAND()
    if os.getenv("CV2X") == "YES-CV2X":
        A35_total_eMMC, consumed_emmc, A35_eMMC_percentage = A35_eMMC_CHN()
        print("China/V2X Version for eMMC layout")
    else:
        A35_total_eMMC, consumed_emmc, A35_eMMC_percentage = A35_eMMC()
        print("Europe Version for eMMC layout")
    A35_total_nor , A35_used_NOR, A35_NOR_percentage = A35_NOR(soc_location, destination)
    A7_total_RAM, A7_consumed_ram, A7_RAM_percentage = A7_RAM()
    A35_total_RAM, A35_consumed_ram, A35_RAM_percentage = A35_RAM()
    components = ['IMX8-NOR', 'IMX8-EMMC', 'IMX8-RAM', 'A7-NAND','A7-RAM']
    used_values = [A35_used_NOR, consumed_emmc, A35_consumed_ram, consumed_nand, A7_consumed_ram]
    used_values = [f"{value} MB" for value in used_values] # with MB value
    available_values = [A35_total_nor,A35_total_eMMC,A35_total_RAM,A7_total_NAND,A7_total_RAM ]
    available_values = [f"{value} MB" for value in available_values] # with MB value
    specified = ["80%","80%","80%","80%","80%"]
    used_values_percentage = [A35_NOR_percentage,A35_eMMC_percentage,A35_RAM_percentage,A7_NAND_percentage,A7_RAM_percentage]
    used_values_percentage = [f"{value} %" for value in used_values_percentage]
    data = {'Components': components, 'USED': used_values,"AVAILABLE": available_values,"Used [%]":used_values_percentage,"Specified %": specified}
    df = pd.DataFrame(data)
    excel_file_path = destination+"\Memory_Layout.xlsx"
    df.to_excel(excel_file_path,index=False)
    print(f"Excel file created at location {destination}")
    remove_test_files(destination)
    end = time.time()
    total_time = end - start
    print(f"Script executed in {str(round(total_time, 2))} seconds")
    sys.exit()
