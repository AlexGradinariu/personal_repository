import optparse
import re
import os,sys

parser = optparse.OptionParser()
parser.add_option('-f', '--file', action="store", dest="filename",help=" text file converted from pcap")
parser.add_option('-r', '--regex', action="store", dest="regex",help=" regex to be searched inside file converted")
options, args = parser.parse_args()

filename = options.filename
regex = str(options.regex)

def check_pcap_traces(regex,file):
    Tos = re.compile(regex)
    secured_tos = 0
    with open(filename,"r",encoding="utf8") as log_pcap:
        for line in log_pcap.readlines():
            if Tos.search(line):
                secured_tos += 1
    if secured_tos != 0:
        print(f"Secured Tos string traces were found as {regex}")
    else:
        print(f"No secured traces as {regex} found in file {file}")


if __name__ == "__main__":
    if not os.path.exists(filename):
        print("Location is invalid!")
        sys.exit(0)
    check_pcap_traces(regex,filename)
    print("Successfully parsed")