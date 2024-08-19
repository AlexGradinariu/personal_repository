import re
import paramiko
import argparse
import time,json
import os

parser = argparse.ArgumentParser(description= "Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)
parser.add_argument('-j', '--json', help='json', dest="json_location", required=True)

args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key
json_location = args.json_location

def get_service_info(command):
    (stdin, stdout, stderr) = client.exec_command(command)
    out=stdout.read().decode('utf-8')
    if out != "None":
        return out
    stdin.close()
    stdout.close()
    stderr.close()
    client.close()
def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client
def get_slices(slicelist):
    list_of_slices = []
    regex = r'(system.*.slice)'
    for item in slicelist.strip().split():
        match = re.search(regex, item)
        if match:
            list_of_slices.append(match.group(1))
    return list_of_slices
def memory_allocation_for_slice(slicelist):
    Current_mem = r"MemoryCurrent=(\d+)"
    Memory_limit = r"MemoryLimit=(\d+)"
    slicedict = {}
    for slice in slicelist:
        slice_info = get_service_info(f"systemctl show {slice} | grep Memory ")
        for line in slice_info.split("\n"):
            if "MemoryCurrent=" in line:
                curnt_mem = re.search(Current_mem,line)
                if curnt_mem:
                    slicedict[slice]=[f'Current Value: {bytes_to_kb(int(curnt_mem.group(1)))} Kb']
            if "MemoryLimit" in line:
                if line.split("=")[1] == 'infinity':
                    slicedict[slice].append('Limit Value: infinity')
                else:
                    limit_mem = re.search(Memory_limit,line)
                    if limit_mem:
                        slicedict[slice].append(f'Limit Value: {bytes_to_kb(int(limit_mem.group(1)))} Kb')
    print("---List with all slices and allocated quota values ---")
    for key,value in slicedict.items():
        print(key,':',value)
    return slicedict
def bytes_to_kb(bytes):
    return "{:.0f}".format(bytes / 1024)
def service_allocation_for_slice(slicelist):
    regex = r"─(.*.service)"
    service_allocation = {}
    for slice in slicelist:
        slice_info = get_service_info(f"systemd-cgls -u {slice} | grep service")
        for line in slice_info.split("\n"):
            match = re.search(regex,line)
            if match:
                if slice in service_allocation.keys():
                    service_allocation[slice].append(match.group(1))
                else :
                    service_allocation[slice] = [match.group(1)]
    print("---List with all slices and service allocation for each slice ---")
    for key,value in service_allocation.items():
        print(key,"holds services:",value)
def compare_cgroups(slice_dict,old_quota):
    new_values_dictionary = {}
    for key,values in slice_dict.items():
        for item in values:
            if 'Limit Value:' in item:
                new_values_dictionary[key]=item
    # Dump the dictionary with only 'Limit Value' into a JSON file
    # with open(r'C:\Users\uidn1902\Desktop\EXT_recovery\imx_quotas', 'w') as json_file:
    #     json.dump(limit_values_dict, json_file)
    # Read the JSON file back
    with open(old_quota,'r') as json_file:
        old_version = json.load(json_file)
    if old_version == new_values_dictionary:
        print("quotas values are unchanged")
    #check for key change
    else:
        print("Values are changed as follows:")
        for key in old_version.keys():
            if key not in new_values_dictionary:
                print(f"Slice {key} with : {old_version[key]} does not exists on the TCU output of slices !")
        for key in new_values_dictionary:
            if key not in old_version:
                print(f"Slice {key} with : {new_values_dictionary[key]} is on the TCU and does not exist in actual quota values !")
        for key,value in new_values_dictionary.items():
            if key in old_version:
                if new_values_dictionary[key] != old_version[key]:
                    print(f"Slice {key} has values {new_values_dictionary[key]} on TCU output and value {old_version[key]} on static quota values !")





if __name__ == "__main__":
    start_time = time.time()
    client = createSSHClient(server, port, user, key)
    list_of_slices = get_slices(get_service_info('systemd-cgls'))
    slice_and_quota_dictionary = memory_allocation_for_slice(list_of_slices)
    service_allocation_for_slice(list_of_slices)
    if os.getenv("CV2X") == "YES-CV2X":
        if port == 23:
            print("---Checking V2X NAD quotas---")
            compare_cgroups(slice_and_quota_dictionary,os.path.join(json_location,"V2X_NAD_quotas.json"))
        elif port == 22:
            print("---Checking V2X IMX quotas---")
            compare_cgroups(slice_and_quota_dictionary,os.path.join(json_location, "V2X_IMX_quotas.json"))
    else :
        if port == 23:
            print("---Checking HIGH NAD quotas---")
            compare_cgroups(slice_and_quota_dictionary,os.path.join(json_location,"HEU_NAD_quotas.json"))
        elif port == 22:
            print("---Checking HIGH IMX quotas---")
            compare_cgroups(slice_and_quota_dictionary,os.path.join(json_location, "HEU_IMX_quotas.json"))
    end_time = time.time()
    print(f"Successfully parsed in {str(end_time - start_time)[0:4]} seconds !")