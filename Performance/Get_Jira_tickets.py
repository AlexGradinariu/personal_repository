import re,json,optparse
from atlassian import Confluence
from requests.auth import HTTPBasicAuth
import requests

parser = optparse.OptionParser()
parser.add_option('-a', '--cfg',action="store", dest="pathToConfigFile",help="filename of messages file (default: messages)", default="messages")
parser.add_option('-b', '--imx',action="store", dest="imx_file",help="file that contains IMX failed messages", default="Failed_Services_IMX.txt")
parser.add_option('-c', '--nad',action="store", dest="nad_file",help="file that contains NAD failed messages", default="Failed_Services.txt")
parser.add_option('-d', '--slx',action="store", dest="selinux_denials",help="file that contains selinux_denials  messages", default="Selinux_Denials.txt")
parser.add_option('-e', '--tckt',action="store", dest="ticket_file",help="file that contains ticket IDs", default="ticket_ids.txt")
options, args = parser.parse_args()

#Test Case Dinamic Config
pathToConfigFile = options.pathToConfigFile
imx_file = options.imx_file
nad_file = options.nad_file
selinux_denials = options.selinux_denials
ticket_file = options.ticket_file

#Jira Config
team = 'DRT15, CPL,TP'
issuetype = 'Defect'
status = 'New, Analyzing, Working, Verifying'
priority = 'Blocker, Critical, Major, Minor'

def get_failed_services(text_file):
    lista_services = set()
    with open(text_file,"r",encoding="utf-8") as file:
        for line in file:
            if "systemd[1]" in line:
                try:
                    service = re.search("(systemd\[1\]:)\s(.*),\scode",line).group(2)
                    lista_services.add(service)
                except : pass
    return lista_services
def get_selinux_denials(text_file):
    list_of_denials = set()
    with open(text_file, "r", encoding="utf-8") as file:
        for line in file:
            if "avc: denied" in line:
                denial = re.search(r'avc:\sdenied.*comm=("(?!(?:ls|sh)")\S+).*\s(capability|path)', line)
                if denial:
                    list_of_denials.add('avc: denied' + " " + f'comm={denial.group(1)}'.replace('"', ''))
    return list_of_denials
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
        password=config["Confluence_Pass"])

def get_ticket_id(issues_detected):
    confluence = get_confluence_access(pathToConfigFile)
    url = "https://jira-iic.zone2.agileci.conti.de/rest/api/2/search"
    auth = HTTPBasicAuth(confluence.username, confluence.password)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = json.dumps({
                             "jql": f'project in ({team}) AND issuetype = {issuetype} AND status in ({status}) AND priority in ({priority}) AND (summary ~ "{issues_detected}" OR description ~ "{issues_detected}" ) ORDER BY updated DESC',
                             "startAt": 0,
                             "maxResults": 1,
                             "fields": [
                                 "summary",
                                 "status",
                                 "assignee"
                             ],
                             })
    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    print(response.status_code)
    buffer = json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(',', ':'))
    if '"key":"DRT15-' in buffer:
        ticket_id = re.search(r'.*"key":"(DRT15-(\d+))"', buffer).group(1)
        ticket_summary = re.search(r'"summary":(.*)', buffer).group(1)
        with open(ticket_file,"a",encoding= "utf-8") as fisier:
            print("Possible issues detected:",sep = "\n",file=fisier)
            print(f"{ticket_id} : {ticket_summary}",sep = "\n",file=fisier)
            print(f"{ticket_id} : {ticket_summary}")
    elif '"key":"CPL-' in buffer:
        ticket_id = re.search(r'.*"key":"(CPL-(\d+))"', buffer).group(1)
        ticket_summary = re.search(r'"summary":(.*)', buffer).group(1)
        with open(ticket_file, "a", encoding="utf-8") as fisier:
            print("Possible issues detected:", sep="\n", file=fisier)
            print(f"{ticket_id} : {ticket_summary}", sep="\n", file=fisier)
            print(f"{ticket_id} : {ticket_summary}")
    elif '"key":"TP-' in buffer:
        ticket_id = re.search(r'.*"key":"(TP-(\d+))"', buffer).group(1)
        ticket_summary = re.search(r'"summary":(.*)', buffer).group(1)
        with open(ticket_file, "a", encoding="utf-8") as fisier:
            print("Possible issues detected:", sep="\n", file=fisier)
            print(f"{ticket_id} : {ticket_summary}", sep="\n", file=fisier)
            print(f"{ticket_id} : {ticket_summary}")


if __name__ == "__main__":
    for issue in get_failed_services(nad_file):
        get_ticket_id(issue)
    for issue in get_failed_services(imx_file):
        get_ticket_id(issue)
    for issue in get_selinux_denials(selinux_denials):
        get_ticket_id(issue)
    print("Successfully parsed")