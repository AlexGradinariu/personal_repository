import re,json
import time
import paramiko
import argparse
import pandas as pd
import requests
from atlassian import Confluence

'''
Every capability of a process is documented at: 
https://confluence.auto.continental.cloud/pages/viewpage.action?spaceKey=DRT15&title=3.+Capabilities
Any above capability should be also found in the following gerrit page: 
https://buic-scm-ias.contiwan.com:8443/gitweb?p=drt15/main.git;a=blob;f=scripts/config-pd-permissions;hb=refs/heads/master

Also ,script bellow is checking if other process have capabilities which are not documented.
Alex G.

- all root capabilities sohuld not be check,by default they have all capabilities
- checking for permitted capabilities ,decode them and check if they match excel confluence page
- check also binary capabilities if are documented

'''

parser = argparse.ArgumentParser(description= "Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)
parser.add_argument('-l', '--path', help='Path', dest="path", required=True)


args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key
excel_path = args.path+"\Capabilities_Deviation.xlsx"


confluenceID="268025145" # ... in upper right corner of conlfunece - > click on page information
filenameConfluence="Capabilities_Deviation.xlsx" #name of attachement
json_location = r"D:\drt16_repo_ct\SYSTEM\drt-lego\tools\Scripts\Networking\measure_config.json"

##########################################################################################################################
#
# Name: get_confluence_access(confluence_auth_path)
#
# Description: This funtions get all authentification information
#
# Inputs: confluence_auth_path - path for json with authentification information
#
# Outputs: -
#
# Notes:
#
##########################################################################################################################

def get_confluence_access(confluence_auth_path):
    """
    Provides the Confluence access object.
    :param confluence_auth_path: Path The path to the JSON file which contains the authorization information.
    :return: Confluence The Confluence access object
    """
    with open(confluence_auth_path) as config_file:
        config = json.load(config_file)

    return Confluence(
        url=config["Confluence_Path"],
        username=config["Confluence_User"],
        password=config["Confluence_Token"])


##########################################################################################################################
#
# Name: download_file(confluence: Confluence,confluenceID,filenameConfluence,Path)
#
# Description: This funtions download csv file from confluence
#
# Inputs: Confluence is attributes for confluence page login
#         confluenceID is confluence page id
#         filenameConfluence is name for file from confluence
#         Path - is path for download
# Outputs: -
#
# Notes:
#
##########################################################################################################################

def download_file(confluence: Confluence, confluenceID, filenameConfluence, Path):
    page_id = confluenceID

    if page_id is None:
        raise ("Could not find the Confluence page!")

    attachments_container = confluence.get_attachments_from_content(page_id, start=0, limit=1000)
    attachments = attachments_container['results']
    attachment_name = filenameConfluence
    for attachment in attachments:

        file_name = attachment['title']
        if file_name == attachment_name:
            download_link = confluence.url + attachment['_links']['download']
            r = requests.get(download_link, auth=(confluence.username, confluence.password))
            print(r)
            if r.status_code == 200:
                with open(Path, "wb") as f:
                    for bits in r.iter_content():
                        f.write(bits)

    # TODO need to add more logging!
    return r

def download_excel_file(confluence: Confluence, Path):
    url = confluence.url
    headers = {"Authorization": f"Bearer {confluence.password}",
        "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers)
        print(f"Responde code : {response.status_code}")
        if response.status_code == 200:
            with open(f"{Path}", "wb") as f:
                for bits in response.iter_content():
                    f.write(bits)
            print("File downloaded successfully!")
        else:
            print("File could not be downloaded, see reponse code !")
    except Exception as e :
        print(f"Exception occured as {e}")

#create ssh client
def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client

#function to return output for any commad
def ssh_command(cmd):
    (stdin, stdout, stderr) = client.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    if out:
        return out
    else:
        return out

def decode_capabilities(cap):
    '''Using function of capsh --decode= value , we decode each capability based on bytes value, example:
    capsh --decode=0000000000001000 = 0x0000000000001000=cap_net_admin ,returning 2nd value from string.'''
    capability_decoded = ssh_command(f"capsh --decode={cap}").split("=")
    return(capability_decoded[1])

#function to get all services running on
def get_process_info():
    list_with_undocumented_processes ={}
    capability_dictionary_TCU = {}
    capability_dictionary_Excel = {}
    count_issue = 0
    #create a dictionary with key as PID and applications as PID name in order to check their capabilities
    regex_pid_procname = "(\d+)\s(.*)"
    pid = []
    pid_names = []
    Services = ssh_command("ps | awk '{print$1,$5}' | grep -E 'usr|conti|opt' | grep -v root")
    for x in Services.splitlines():
        l =re.search(regex_pid_procname,x.strip())
        try:
            pid.append(l.group(1))
            pid_names.append(l.group(2))
        except Exception as e:
            print(f"Exception occured as {e} ! ")
    dictionary = dict(zip(pid, pid_names))
    #create whitelist services that are running as root so they can be excluded:
    root_services = ssh_command("ps | grep root | awk '{print$1}'")
    root_services_list = []
    for services in root_services.splitlines():
        root_services_list.append(services)
    '''remove services that are as root user items'''
    for pid,name in list(dictionary.items()):
        if pid in root_services_list:
            del dictionary[pid]
    '''remove items from white list : find the pid of the item and remove the pid as key'''
    white_list = ['/usr/bin/netmgrd','/usr/bin/QCMAP_ConnectionManager']
    temporary_key_deletion = []
    for key, value in dictionary.items():
        if value in white_list:
            temporary_key_deletion.append(key)
    for key in temporary_key_deletion:
        del dictionary[key]
    # check all other proceesses if they have unset capabilities
    for x in dictionary.keys():
        a = ssh_command(f"cat /proc/{x}/status | grep CapPrm:" + "| awk '{print$2}'")
        if "0000000000000000" not in a:
            if dictionary[x] in list(df["binary"]):
                print(f"Start checking process '{dictionary[x]}'...",flush=True)
                cap_var= decode_capabilities(a).strip().replace('\n','').split(",")
                print(f"Process '{dictionary[x]}' has permitted capability as '{cap_var}' on TCU check ! ",flush=True)
                print(f"Process '{dictionary[x]}' has permitted capability as '{function_excel_capabilities(dictionary[x])}' on Confluence Excel File !",flush=True)
                capability_dictionary_TCU[dictionary[x]] = cap_var
                capability_dictionary_Excel[dictionary[x]] = function_excel_capabilities(dictionary[x])
                items_not_inList = [item for item in capability_dictionary_TCU[dictionary[x]] if item not in capability_dictionary_Excel[dictionary[x]]]
                if len(items_not_inList) == 0:
                    print(f"For process '{dictionary[x]} capabilities permitted on TCU are matching documented specifications, allgood ! ")
                    print("\n\n")
                else:
                    print(f"For process '{dictionary[x]} capabilities are not matching specifications ! please check")
                    count_issue += 1
                    print("\n\n")
            else :
                list_with_undocumented_processes[(dictionary[x])] = decode_capabilities(a)
                count_issue += 1
    if count_issue == 0:
        print("----------",flush=True)
        print("No issues found for process capabilities !",flush=True)
    else:
        print("----------",flush=True)
        print("Process capabilities issues were found, please check all items !",flush=True)
    if len(list_with_undocumented_processes) != 0:
        print("Bellow processes are not documented in Confluence Excel page, check : https://confluence-iic.zone2.agileci.conti.de/pages/viewpage.action?spaceKey=DRT15&title=3.+Capabilities  ")
        for key, value in list_with_undocumented_processes.items():
            print("Process :",key,"with capability :" ,value)

#create a function that will check for binaries capability
def check_binary_capabilities():
    "Create a list with all accepted capabilities"
    ls_of_acc_capability = ['/tst/bin/m4_uad_test']
    issues_binary = 0
    df = pd.read_excel(excel_path, usecols="B:E")
    for x in df["binary"].dropna():
        ls_of_acc_capability.append(x)
    '''get all binaries capability files from the system'''
    capabilities = ssh_command("getcap -r / 2>/dev/null | awk '{print$1}'")
    list_binary_capabilities = capabilities.splitlines()
    '''Remove all accepted capabilities from what system is outputs'''
    for item in list_binary_capabilities:
        if item not in ls_of_acc_capability:
            print(f"Following undocumented plain binary: '{item}' has capabilities as : {ssh_command(f'getcap -r {item}').split('=')[1]}",flush=True)
            issues_binary += 1
    if issues_binary == 0:
        print("No issues found for binary capabilities !", flush=True)
    else:
        print("ALl binaries with capabilities must be documented in confluence at : https://confluence.auto.continental.cloud/pages/viewpage.action?spaceKey=DRT15&title=3.+Capabilities !",flush=True)

def function_excel_capabilities(service):
    values = ""
    if port == 23:
        df =pd.read_excel(excel_path,usecols="B:E").fillna("")
        df = df.set_index("binary")
        df=df.loc[service]
        try:
            if df["NAD"].lower():
                values += (df["NAD"].lower())
        except: pass
        finally:
            if (df["Both"].lower()):
                values +=(df["Both"].lower())
        if "," in values:
            values_a = values.split(",")
        else:
            values_a = []
            values_a.append(values)
        return(values_a)
    else:
        df = pd.read_excel(excel_path, usecols="B:E").fillna("")
        df = df.set_index("binary")
        df = df.loc[service]
        try:
            if (df["iMX"].lower()) :
                values +=(df["iMX"].lower())
        except:pass
        finally:
            if (df["Both"].lower()):
                values +=(df["Both"].lower())
        if "," in values:
            values_a = values.split(",")
        else:
            values_a = []
            values_a.append(values)
        return(values_a)


if __name__ == "__main__":
    client = createSSHClient(server, port, user, key)
    start_time = time.time()
    confluence = get_confluence_access(json_location)
    ##download_file(confluence, confluenceID, filenameConfluence, excel_path) '''not used anymore'''
    download_excel_file(confluence, excel_path)
    df = pd.read_excel(excel_path,usecols="B:E").fillna("")
    get_process_info()
    print("Process capabilities check has finished,script continuing ...")
    check_binary_capabilities()
    end_time = time.time()
    print(f"Successfully parsed in {str(end_time-start_time)[0:4]} seconds !")