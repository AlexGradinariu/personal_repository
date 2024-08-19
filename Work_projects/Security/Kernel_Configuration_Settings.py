import pandas as pd
import optparse,json,requests
from atlassian import Confluence

parser = optparse.OptionParser()
parser.add_option('-r', '--a35excel;', action="store", dest="excel_location", help="Location for A35 Kernel Settings Excel File")
parser.add_option('-a', '--a35txt', action="store", dest="text_location", help="Location for A35 Kernel Settings Text File")
parser.add_option('-b', '--a7txt', action= "store", dest= "text_location_A7", help= "Location for A7 Kernel Settings Text File" )
options, args = parser.parse_args()

Excel_path = str(options.excel_location)
IMX_Cfg = str(options.text_location)
NAD_cfg = str(options.text_location_A7)
json_location = r"D:\drt16_repo_ct\SYSTEM\drt-lego\tools\Scripts\Networking\measure_config.json"
url_NAD = "https://confluence.auto.continental.cloud/download/attachments/1052331013/Kernel_Settings_NAD.xlsx?api=v2"
url_IMX = "https://confluence.auto.continental.cloud/download/attachments/1052331013/Kernel_Settings_IMX8.xlsx?api=v2"
'''https://confluence.auto.continental.cloud/display/DRT15/Kernel+config'''

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

def download_excel_file(confluence: Confluence, Path,url_path):
    headers = {"Authorization": f"Bearer {confluence.password}",
        "Content-Type": "application/json"}
    try:
        response = requests.get(url_path, headers=headers)
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


def A35_get_kernel_settings(file,argument):
    df = pd.read_excel(file,sheet_name= "Sheet1",usecols="A:B")
    filtered_df = df[df["Kernel_nam"].str.contains("CONFIG_", na=False) & (df["Value"] == argument)]
    return list(x for x in filtered_df["Kernel_nam"])
    # with open("A35.txt", "a") as file:
    #     for x in list_of_config_elements:
    #         A35_config_elements.append(x)
    #         file.write(x)
    #         file.write("\n")


def A7_get_kernel_settings(file,argument):
    df = pd.read_excel(file,sheet_name= "Sheet1",usecols="A:B")
    filtered_df = df[df["Kernel_nam"].str.contains("CONFIG_", na=False) & (df["Value"] == argument)]
    return list(x for x in filtered_df["Kernel_nam"])


def A7_baseline_kernel_settings(file,argument):
    kernel_settings = []
    if argument == "y":
        with open(file) as txtfile:
            for line in txtfile:
                if "=y" in line:
                    configs = line.split("=") # returns a list
                    kernel_settings.append(configs[0].strip())#append 1st element of the list
    elif argument == "N":
        with open(file) as txtfile:
            for line in txtfile:
                if "=n" in line:
                    configs = line.split("=") # returns a list
                    kernel_settings.append(configs[0].strip())#append 1st element of the list
                if "is not set" in line:
                    configs = line.split("is not set")
                    kernel_settings.append(configs[0].strip("#").strip(" "))  # append 1st element of the list
    return kernel_settings
def A35_baseline_kernel_settings(file,argument):
    kernel_settings = []
    if argument == "y":
        with open(file) as txtfile:
            for line in txtfile:
                if "=y" in line:
                    configs = line.split("=")  # returns a list
                    kernel_settings.append(configs[0].strip())  # append 1st element of the list
    elif argument == "N":
        with open(file) as txtfile:
            for line in txtfile:
                if "=n" in line:
                    configs = line.split("=")  # returns a list
                    kernel_settings.append(configs[0].strip())  # append 1st element of the list
                if "is not set" in line:
                    configs = line.split("is not set")
                    kernel_settings.append(configs[0].strip("#").strip(" "))  # append 1st element of the list
    return kernel_settings

def compare_lists(list1, list2,node):
    results = [x for x in list1 if x not in list2]
    if len(results) != 0:
        print(f"The following kernel config are present in the {node} - Security Excel file but not also in baseline configuration !")
        print(*results,sep='\n')
        print(f"Kernel configs are not matching for {node} !")
    else :
        print(f"Kernel configs are matching for {node} !")

def compare_lists_N(Excel, TXT_file, node):
    results = [x for x in Excel if x in TXT_file]
    if len(results) != 0:
        print(
            f"The following kernel config are present in the Security Excel for {node} with N argument - file can be found with Y argument in baseline configuration !")
        print(*results, sep='\n')
        print(f"Kernel configs are not matching for {node} !")
    else:
        print(f"Kernel configs are matching for {node} !")


if __name__ == "__main__":
    imx_white_list = ['CONFIG_SLUB_DEBUG_ON','CONFIG_USB_ROLE_SWITCH']
    confluence = get_confluence_access(json_location)
    # download_file(confluence, confluenceID, filenameConfluence, excel_path)
    download_excel_file(confluence, Excel_path + r"\NAD.xlsx",url_NAD) #for NAD Excel
    download_excel_file(confluence, Excel_path + r"\IMX.xlsx", url_IMX)  # for IMX Excel
    print("Kernel Settings with Y argument ")
    print("----")
    '''Take Y arguments for give kernel settings'''
    #Excel configs
    A35_config_elements_Y = A35_get_kernel_settings(Excel_path + r"\IMX.xlsx", "y")
    for element in imx_white_list:
        if element in A35_config_elements_Y:
            A35_config_elements_Y.remove(element)
    A7_config_elements = A7_get_kernel_settings(Excel_path + r"\NAD.xlsx","y")
    #baseline configs
    A7_kernel_config = A7_baseline_kernel_settings(NAD_cfg,"y")
    A35_kernel_config = A35_baseline_kernel_settings(IMX_Cfg,"y")
    #compare lists between Excel and TXT File
    compare_lists(A7_config_elements,A7_kernel_config,"NAD")
    compare_lists(A35_config_elements_Y, A35_kernel_config, "IMX")
    '''Take N arguments for give kernel settings'''
    print("\n")
    print("Kernel Settings with N argument ")
    print("----")
    A35_config_elements_N = A35_get_kernel_settings(Excel_path + r"\IMX.xlsx", "N")
    for element in imx_white_list:
        if element in A35_config_elements_N:
            A35_config_elements_N.remove(element)
    A7_config_elements_N = A7_get_kernel_settings(Excel_path + r"\NAD.xlsx", "N")
    # compare lists between Excel and TXT File
    compare_lists_N(A7_config_elements_N, A7_kernel_config, "NAD")
    compare_lists_N(A35_config_elements_N, A35_kernel_config, "IMX")
    print("Successfully parsed")