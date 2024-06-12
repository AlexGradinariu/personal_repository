import paramiko
import argparse,time

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


args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key

#create ssh client
def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client

#function that will return any given command
def ssh_command(cmd):
    (stdin, stdout, stderr) = ssh_client.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    if out:
        return out
    else:
        return out

#function that will output all services that are using dbus communication
def get_services_using_dbus():
    # Populate a list with all available services that are using dbus communication
    services_using_bus = []
    Services = ssh_command("COLUMNS=300 busctl | awk '{print$6}'")
    for x in Services.splitlines():
        if len(x) != 0:
            services_using_bus.append(x)
    services_using_bus = list(set(services_using_bus))#to  remove duplicates
    #trim the list
    if 'UNIT' in services_using_bus:
        services_using_bus.remove("UNIT")
    if 'init.scope' in services_using_bus:
        services_using_bus.remove('init.scope')
    if '-' in services_using_bus:
        services_using_bus.remove('-')
    return services_using_bus


#get a dictionary with all services and their dbusname addresses and also services that needs to be checked
def get_services_for_dbus_name(one_list_of_services):
    services_with_dbusname = {}
    for x in one_list_of_services:
        dbus =  ssh_command(f"systemctl cat {x} | grep 'BusName='")
        # if len(dbus) == 0:
            # print(f"The following service {x} does not have a dbusname configuration, must check the .xml file ! ")
        if len(dbus) != 0:
            print(f"Service {x} has a dbusname configuration, will be checked inside /etc/dbus-1/system.d for .conf files")
            services_with_dbusname[x] = dbus.strip().split("=")[1]
            dictionary_to_beused[x] = dbus.strip().split("=")[1]
    return services_with_dbusname

def check_for_dbus_name(one_list_of_services):
    '''Pass to this function a dictionary with service name and dbus name address:
    It will check if the dbus name exists at /etc/dbus-1/system.d and if it is exists it must not have a default context policy
    Fucntion get_services_for_dbus_name() should be able to pass such a dictionary to this function'''
    list_of_configs = [] # create list of .conf files
    list_of_services = [] #create lists of services
    for service in one_list_of_services:
        conf = ssh_command(f"grep -r {one_list_of_services[service]} /etc/dbus-1/system.d " + "| awk '{print$1}'")
        if len(conf) == 0:
            print(f'Service {service} for {one_list_of_services[service]} dbusname  cannot be found in  .conf files -- NOK !')
        else:
            #create temporary list of unique lines, as conf will output multiple duplicated lines.
            lines = conf.strip().split('\n')
            uniques = set(lines)
            for conf in uniques:
                list_of_configs.append(conf.strip(':'))
                list_of_services.append(service)
    tuple_services_config_files=zip(list_of_services,list_of_configs)
    for count, tp in enumerate(tuple_services_config_files):
        context_policy = ssh_command(f"cat {tp[1]} | grep 'policy context'")
        if "default" in context_policy.strip():
            print(f"Service {tp[0]} has dbus name in {list(list_of_configs)[count]} file but the context policy is {context_policy.strip()} -- NOK ! ")
        # else:
        #     print(f"Service {tp[0]} has dbus name in {list(list_of_configs)[count]} file and the context file is not default ! --all good! ")

if __name__ == '__main__':
    white_list_of_services = ['valensd.service','xdelta_uad.service']
    ssh_client = createSSHClient(server, port, user, key)
    start_time = time.time()
    dictionary_to_beused = {}
    print("---------Check services for dbus name presence------------")
    get_services_for_dbus_name(get_services_using_dbus())
    print("---------Check services for dbus conf file presence------------")
    #removing items as per whitelist
    for service in white_list_of_services:
        if service in dictionary_to_beused:
            try:
                print('Deleting service {} from dictionary as per whitelist !'.format(service))
                del dictionary_to_beused[service]
            except KeyError:
                print(f"Error occurred while removing service {service} from whitelist!")
    check_for_dbus_name(dictionary_to_beused)
    end_time = time.time()
    print(f"Successfully parsed in {str(end_time - start_time)[0:4]} seconds !")
    ssh_client.close()

