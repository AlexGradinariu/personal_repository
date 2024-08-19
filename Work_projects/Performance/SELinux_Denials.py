import optparse
import os
import sys,re

def servicii_crapate(filename):
    white_list = ['comm="ifconfig".*context.*ifconfig','comm="usb_init".*context.*hal-fs-qcom_usb_tp_t','comm="conti-v2x-apps".*context.system_u']
    for root, dirs, files in os.walk(filename):
        for file in files:
            if file.startswith("messages"):
                with open(os.path.join(root, file), 'r', encoding="latin-1") as filer:
                    with open(os.path.join(location, "Selinux_Denials.txt"), 'a') as fw:
                        fw.write("\n")
                        fw.write("Fails are from following file {}: ".format(os.path.join(root, file)))
                        fw.write("\n")
                        for line in filer:
                            if "avc: denied" in line:
                                if not any(re.search(regex, line) for regex in white_list):
                                    fw.write("SELINUX Denials as       {}".format(line))
                                    print(f'SELINUX Denials found in {os.path.join(root, file)}')
                                else:
                                    print("No selinux denials found !")

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file',
        action="store", dest="filename",
        help="filename of messages file (default: messages)", default="messages")

    parser.add_option('-d', '--destination',
        action="store", dest="location")
    options, args = parser.parse_args()
    filename = options.filename
    location = str(options.location)
    if not os.path.exists(filename):
        print("Location is invalid!")
        sys.exit(0)
    servicii_crapate(filename)
    print("Successfully parsed")
