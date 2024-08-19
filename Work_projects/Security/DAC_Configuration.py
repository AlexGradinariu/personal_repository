import pandas as pd
import os.path
import paramiko
import argparse,sys,re
import json
import requests,time
# import urllib3
# urllib3.disable_warnings()
'''
This script was created in order to check Custom File Mode and DAC Confingurations.
Used Files:
Gerrit:
imx : https://buic-scm-fr.contiwan.com:8443/gitweb?p=drt15/security-conf/imx8/restrict-uid-conf.git;a=blob_plain;f=all-filemodes-input.csv;hb=refs/heads/master
nad : https://buic-scm-fr.contiwan.com:8443/gitweb?p=drt15/security-conf/nad/restrict-uid-conf.git;a=blob_plain;f=all-filemodes-input.csv;hb=refs/heads/master
Local Files:
pck-size.txt file generated at each build
How it works:
Automatically copies the content from above pages into .txt format, parses the .txt files and create 2 excel files for NAD and IMX.
Compares the content of the theoretical content from above Excel files with actual content from TCU
'''


parser = argparse.ArgumentParser(description= "Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)
parser.add_argument('-e', '--excel_f', help="excel_path", dest="excel_f", required=True)
parser.add_argument('-a', '--pck', help="pck_size", dest="pck", required=True)
parser.add_argument('-l', '--local', help="local_path_from_atp", dest="local", required=True)
parser.add_argument('-c', '--check', help="path to local autotenthication json", dest="auth", required=True)

args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key
excel_path = args.excel_f
pck_path =args.pck
location = args.local
gerrit_auth_path = args.auth

#prepare environment, copy gerrit text files and convert them to excel

def remove_empty_list(d : dict ) -> dict:
    return {k:v  for k,v in d.items() if  v }

def get_gerrit_access(gerrit_auth_path):
    """
    Provides the Confluence access object.
    : param confluence_auth_path: Path The path to the JSON file which contains the authorization information.
    : return: Confluence The Confluence access object
    """
    with open(gerrit_auth_path) as config_file:
        config = json.load(config_file)
        url_imx=config["gerrit_imx_file"]
        url_nad=config["gerrit_nad_file"]
        username=config["Confluence_User"]
        password=config["Confluence_Pass"]
    return (url_imx,url_nad,username,password)

def creeare_lista_servicii(url,file):
    gerrit_content_list = []
    #create payload environment so we can login to gerrit page
    page_loggin = r"https://buic-scm-fr.contiwan.com:8443/login/%2Fgitweb%3Fp%3Ddrt15%2Fsecurity-conf%2Fnad%2Frestrict-uid-conf.git"
    payload ={"username":get_gerrit_access(gerrit_auth_path)[2],"password":get_gerrit_access(gerrit_auth_path)[3]}
    session = requests.Session()
    session.post(page_loggin,data=payload)
    r = session.get(url)
    if r.status_code == 200:
        print(f"Response status is : {r.status_code}")
        print("File was sucessfully copied from gerrit repository, continuing script...")
    with open(os.path.join(location,file),"w",encoding="utf-8") as copied_file:
        copied_file.write(r.text)
    #create text file with content from gerrit in order to create excel file
    try:
        path = os.path.join(location,"NAD_filemode.xlsx") if  "nad" in file else  os.path.join(location,"IMX_filemode.xlsx")
        with open(os.path.join(location,file), 'r',encoding="utf-8") as fisier :
            for line in fisier:
                if "/" and "f" in line.split():
                    gerrit_content_list.append(line)
        with open(os.path.join(location, file), 'r',encoding="utf-8") as fisier:
            for line in fisier:
                if "/sota" in line.split():
                    gerrit_content_list.append(line)
        gerrit_content_list.pop(0) # to remove 1st wrong service
        '''removing wrong content file with 000 octal mode'''
        wrong_list = []
        for x in gerrit_content_list:
            if "000" in x:
                wrong_list.append(x)
            if "Type" in x:
                wrong_list.append(x)
        for x in wrong_list:
            gerrit_content_list.remove(x)
        servicii = []
        octal = []
        owner = []
        group = []
        for x in gerrit_content_list:
            servicii.append(x.strip("#").split()[0]) # to get rid of all commented #
            octal.append(x.split()[2])
            owner.append(x.split()[3])
            group.append(x.split()[4])
        # Create DataFrame from multiple lists
        writer = pd.ExcelWriter(path, engine="xlsxwriter")
        columns = ["Services","octal_rights","ownername","groupname"]
        df = pd.DataFrame(list(zip(servicii,octal,owner,group)), columns=columns)
        df.to_excel(writer,sheet_name="Sheet1",index=False) # to remove column index
        writer.close()
        print("Excel file successfully created !")
    except Exception as e :
        print(f"Exception occured as {e} ! ")

#function created to convert from digits to octal , 440 = 'r--r-----'
def get_access_rights(list):
    octal_rigts = {0: "---", 1: "--x", 2: "-w-", 4: "r--", 6: "rw-", 3: "-wx", 5: "r-x", 7: "rwx"}
    group = str(list)[0]
    owner = str(list)[1]
    others = str(list)[2]
    file_permision = octal_rigts[int(group)] + octal_rigts[int(owner)] + octal_rigts[int(others)]
    return(file_permision)
def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client

def get_service_info(command, awk):
    (stdin, stdout, stderr) = client.exec_command(f"ls -la {command}"+"| awk '{print $" + f"{awk}"+"; }'")
    out=stdout.read().decode('utf-8')
    if out != "None":
        return out


#check permisions for owner
def check_owner_permisions():
    # Create a dictionary with values taken from Excel File
    print("Checking was started for Owner verification...")
    for x in df["Services"]:
        lista_servicii_excel.append(x)
    for x in df["ownername"]:
        group_name_list.append(x[:8])
    dictionar_excel = dict(zip(lista_servicii_excel, group_name_list))
    #Create a dictionary with values taken from TCU
    owner = []
    # Get Owner name from TCU
    for x in dictionar_excel.keys():
        owner.append(get_service_info(x, 3).strip())
    dictionar_tcu = dict(zip(lista_servicii_excel,owner))
    empty_values_dictionary = {k: v for k, v in dictionar_tcu.items() if
                               not v}  # return only false values of v,meaning only empty values
    dictionar_tcu = remove_empty_list(dictionar_tcu)  # re write dictionary without any empty keys
    #Check differences:
    differences = {} #values different on TCU Side
    for key in dictionar_excel:
        if (key in dictionar_tcu and dictionar_excel[key] != dictionar_tcu[key]):
            differences[key]=dictionar_tcu[key]
    issues =list(differences.keys())
    print("--------------Owner verification----------------")
    if len(issues) == 0:
        print("No issues during Owner verification! ")
    else:
        for x in issues:
            print(f"For the following service: {x}")
            print(f"Owner found in Gerrit Documentation file is: '{dictionar_excel[x]}' but the value taken out of TCU is: '{differences[x] if len(differences[x]) > 0 else 'Blank'}'")
    '''Cleanup action not required anymore'''
    # if len(empty_values_dictionary) != 0:
    #     print(
    #         "Following items must be part of a cleanup process,please open a ticket for it,check corresponding vcs file from script !")
    #     print(f"{list(empty_values_dictionary.keys())}")
    # else:
    #     print('Cleanup process not required!')
#check permisions for group
def check_group_permisions():
    # Create a dictionary with values taken from Excel File
    print("Checking was started for Group verification...")
    for x in df["Services"]:
        lista_servicii_excel.append(x)
    for x in df["groupname"]:
        group_name_list.append(x[:8])#last value not included
    dictionar_excel = dict(zip(lista_servicii_excel, group_name_list))
    #Create a dictionary with values taken from TCU
    group = []
    # Get Group name from TCU
    for x in dictionar_excel.keys():
        group.append(get_service_info(x, 4).strip())
    dictionar_tcu = dict(zip(lista_servicii_excel,group))
    empty_values_dictionary = {k: v for k, v in dictionar_tcu.items() if not v}  # return only false values of v,meaning only empty values
    dictionar_tcu = remove_empty_list(dictionar_tcu)  # re write dictionary without any empty keys
    #Check differences:
    differences = {} #values different on TCU Side
    for key in dictionar_excel:
        if (key in dictionar_tcu and dictionar_excel[key] != dictionar_tcu[key]):
            differences[key]=dictionar_tcu[key]
    issues =list(differences.keys())
    print("-------------Group verification-----------------")
    if len(issues) == 0:
        print("No issues during Groups verification! ")
    else:
        for x in issues:
            print(f"For the following service: {x}")
            print(f"Group found in Gerrit Documentation file is: '{dictionar_excel[x]}' but the value taken out of TCU is: '{differences[x] if len(differences[x]) > 0 else 'Blank'}'")
    '''Cleanup action not required'''
    # if len(empty_values_dictionary) != 0:
    #     print(
    #         "Following items must be part of a cleanup process,please open a ticket for it,check corresponding vcs file from script !")
    #     print(f"{list(empty_values_dictionary.keys())}")
    # else:
    #     print('Cleanup process not required!')
#check octal permisions
def check_file_permisions():
    # Create a dictionary with values taken from Excel File,converting from digits to octal values
    print("Checking was started for File Permisions verification...")
    for x in df["Services"]:
        lista_servicii_excel.append(x)
    for x in df["octal_rights"]:
        group_name_list.append(get_access_rights(x))
    dictionar_excel = dict(zip(lista_servicii_excel, group_name_list))
    #Create a dictionary with values taken from TCU via ssh
    octal = []
    # Get Group name from TCU
    for x in dictionar_excel.keys():
        octal.append(get_service_info(x, 1).strip()[1:10]) # values taken without first character
    dictionar_tcu = dict(zip(lista_servicii_excel,octal))
    empty_values_dictionary = {k:v for k,v in dictionar_tcu.items() if not v} #return only false values of v,meaning only empty values
    dictionar_tcu = remove_empty_list(dictionar_tcu) #re write dictionary without any empty keys
    # #Check differences:
    differences = {} #values different on TCU Side
    for key in dictionar_excel:
        if (key in dictionar_tcu and dictionar_excel[key] != dictionar_tcu[key]):
            differences[key]=dictionar_tcu[key]
    issues =list(differences.keys())
    print("-------------File Permisions verification-----------------")
    if len(issues) == 0:
        print("No issues during File Permisions verification! ")
    else:
        for x in issues:
            print(f"For the following service: {x}")
            print(f"File permisions found in Gerrit Documentation file is: '{dictionar_excel[x]}' but the value taken out of TCU is: '{differences[x] if len(differences[x]) > 0 else 'Blank'}'")
    '''Cleanup action not required'''
    # if len(empty_values_dictionary) != 0:
    #     print("Following items must be part of a cleanup process,please open a ticket for it,check corresponding vcs file from script !")
    #     print(f"{list(empty_values_dictionary.keys())}")
    # else:
    #     print('Cleanup process not required!')
#Function created in order to check if all the files declared at D:\DRT15_CT\extra_files\soc\metrics\pkg-size.txt are also documented in gerrit as page provided above
def cross_check_package_size(path_to_pck_txt):
    data = []
    df_data = []
    #create list with pck_size lines
    print("Checking was started for cross_check_package_size...")
    with open(path_to_pck_txt,"r",encoding="utf8") as file:
        for x in file:
            if "<warning>" in x:
                a = x.split("|")
                data.append(a[8].strip())
    # create list with df lines
    for x in df["Services"]:
        df_data.append(x)
    #check if lines from pck size in df lines
    print("-------------Cross_check_package_size-----------------")
    for x in data:
        if x.strip() in df_data:
            print(f"Following services '{x}' are documented in system with <warning> pkg-size.txt file! ")
        else:
            print(f"Following services '{x}' are NOT documented in system pkg-size.txt file! ")

def check_rootfs_vs_pcksizetxt(path_to_pck_txt):
    list_of_TCU_packages = []
    list_of_pck_packages = set()
    (stdin, stdout, stderr) = client.exec_command(f"find / -xdev -type f ")
    out = stdout.read().decode('utf-8')
    if out :
        for line in out.split("\n"):
            list_of_TCU_packages.append(line)
    with open(path_to_pck_txt,"r",encoding="utf8") as file:
        pattern = r'\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|\s+(-?\S+)\s+\|'
        for line in file.readlines():
            match = re.search(pattern,line)
            if match:
                list_of_pck_packages.add(match.group(1))
    #search if itesm from tcu are presen in pckg.txt file
    for item in list_of_pck_packages:
        if item in list_of_pck_packages:
            continue
        else:
            print(f"{item} from TCU is not found in {path_to_pck_txt} file !Please check...")


if __name__ == "__main__":
    start_time = time.time()
    client = createSSHClient(server, port, user, key)
    if port == 23 :
        creeare_lista_servicii(get_gerrit_access(gerrit_auth_path)[1], "nad_restrict_uid.txt")
        print("Start Checking NAD Node...")
    else:
        creeare_lista_servicii(get_gerrit_access(gerrit_auth_path)[0], "imx_restrict_uid.txt")
        print("Start Checking IMX Node...")
    # #Parse excel files and do the actual checking
    df = pd.read_excel(excel_path,index_col=None)
    df.columns =["Services","octal_rights","ownername","groupname"]
    lista_servicii_excel = []
    group_name_list = []
    if not os.path.exists(excel_path):
        print("Location for Excel file is invalid!")
        sys.exit(0)
    if not os.path.exists(pck_path):
        print("Location for pck_size file is invalid!")
        sys.exit(0)
    check_file_permisions()
    check_group_permisions()
    check_owner_permisions()
    cross_check_package_size(pck_path)
    check_rootfs_vs_pcksizetxt(pck_path)
    end_time = time.time()
    print(f"Successfully parsed in {str(end_time - start_time)[0:4]} seconds !")