import paramiko, argparse
from scp import re

parser = argparse.ArgumentParser(description="Parsing some numbers")
parser.add_argument('-s', '--ip', help='IP', dest="ip", required=True)
parser.add_argument('-p', '--port', help='Port', dest="port", required=True)
parser.add_argument('-u', '--user', help='user', dest="user", required=True)
parser.add_argument('-k', '--key', help='Key', dest="key", required=True)

args = parser.parse_args()
server = args.ip
port = int(args.port)
user = args.user
key = args.key

def createSSHClient(server, port, user, key):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, key_filename=key)
    return client

def call_cmd(cmd):
    (stdin, stdout, stderr) = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    if out:
        # print(out.replace("Ã¢Â—Â", ""))  # only for case "systemctl --failed"
        return out
        stdin.close()
        stdout.close()
        stderr.close()
        ssh.close()

def check_udif(tcu_path):
    # Extract into a list every services that runs under conti-drt.
        drt_applications = call_cmd(f"grep -Eri 'ExecStart=.*(/opt/conti|/opt/conti-drt)/bin/' {tcu_path}").split("\n")
        AmbientCapabilities = []
        CapabilityBoundingSet = []
        services_started_by_opt_applications = set()
        for service in drt_applications:
            regex = "(.*)/(.*):ExecStart"
            match = re.search(regex, service.lstrip())
            if match:
                services_started_by_opt_applications.add(match.group(2))

# Extract a list with "AmbientCapabilities" of every process under systemd_services
        systemd_ambientcapabilities = call_cmd(f"grep -ri 'AmbientCapabilities' {tcu_path} | grep -v 'grep'").split("\n")
        for service in systemd_ambientcapabilities:
            regex = "(.*)\/(.*):Ambient"
            match = re.search(regex, service.lstrip(" "))
            if match:
                AmbientCapabilities.append(match.group(2))


# Extract a list with "CapabilityBoundingSet" of every process under systemd_services
        systemd_CapabilityBoundingSet = call_cmd(f"grep -ri 'CapabilityBoundingSet' {tcu_path} | grep -v 'grep'").split("\n")
        for service in systemd_CapabilityBoundingSet:
            regex = "(.*)\/(.*):Capability"
            match = re.search(regex, service.lstrip(" "))
            if match:
                CapabilityBoundingSet.append(match.group(2))
#remove whitelisted services as they are deviations accepted by MB - https://jira-iic.zone2.agileci.conti.de/browse/DRT15-62450
        for service in white_list:
            try:
                services_started_by_opt_applications.remove(service)
            except:pass
#Check if any opt service is using systemd feature AmbientCapabilities:
        for service in services_started_by_opt_applications:
            if service in AmbientCapabilities:
                print(f"The following service '{service}' is using AmbientCapabilities from {tcu_path}")

# Check if any opt service is using systemd feature CapabilityBoundingSet:
        for service in services_started_by_opt_applications:
            if service in CapabilityBoundingSet:
                print(f"The following service '{service}' is using CapabilityBoundingSet from {tcu_path}")

if __name__ == "__main__":
    white_list = ['evaluate-engmode.service','refreshLogLevel.service','set_global_log_level@.service'] #https://jira-iic.zone2.agileci.conti.de/browse/DRT15-62450
    ssh = createSSHClient(server, port, user, key)
    check_udif('/lib/systemd/system')
    print("\n====================================END===================================================\n")