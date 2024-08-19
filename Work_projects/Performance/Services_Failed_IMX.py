import optparse
import os, sys,re

def servicii_crapate(filename):
	match = re.compile("'reboot'.*(pid\s\w+).\sinvoked:|'poweroff'.*(pid\s\w+).\sinvoked:|'halt'.*(pid\s\w+).\sinvoked:")
	match1 = re.compile("LCPM\sapplication.*Cannot\sregister\sapp")
	for root, dirs, files in os.walk(filename):
		for file in files:
			if file.startswith("messages"):
				with open(os.path.join(root, file), 'r', encoding="latin-1") as filer:
					with open(os.path.join(location, "Failed_Services_IMX.txt"), 'a') as fw:
						if "IMX_LOGS" in os.path.join(root, file):
							fw.write("\n")
							fw.write("Fails are from following file {}: ".format(os.path.join(root, file)))
							fw.write("\n")
							for line in filer:
								if "Unit entered failed state" in line:
									fw.write("Application crashdump situation       {}".format(line))
								if "Failed with result" in line:
									if any(re.search(regex, line) for regex in	white_list_regex):
										continue
									else:
										fw.write("Application crashdump situation       {}".format(line))
								if "tpSYS_stackTace" in line:
									fw.write("Application crashdump situation       {}".format(line))
								if "Main process exited" in line:
									if any(re.search(regex, line) for regex in	white_list_regex):
										continue
									else:
										fw.write("Application crashdump situation       {}".format(line))
								if "code=killed" in line:
									if any(re.search(regex, line) for regex in	white_list_regex):
										continue
									else:
										fw.write("Application crashdump situation       {}".format(line))
								if "systemd[1]: Forcibly rebooting as result of failure" in line:
									fw.write("System reset situation       {}".format(line))
								if "systemd[1]: Failed to start" in line:
									fw.write("Application reset situation       {}".format(line))
								if "out of memory: Kill process" in line:
									fw.write("Application Out of Memory limit situation      {}".format(line))
								if "Invalid rule /lib/udev/rules.d" in line:
									fw.write("Application crashdump situation       {}".format(line))
								if ": Failed at step EXEC" in line:
									fw.write("Application crashdump situation       {}".format(line))
								a = match.search(line)
								if a:
									fw.write("Application crashdump situation       {}".format(line))
								b = match1.search(line)
								if b:
									fw.write("Application crashdump situation       {}".format(line))

def COM_Port_Failures(filename):
	UBIFS_corruption = re.compile("UBIFS\serror.*bad\snode")
	for root, dirs, files in os.walk(filename):
		for file in files:
			if file.startswith("SerialCOM"):
				with open(os.path.join(root, file), 'r', encoding="latin-1") as filer:
					with open(os.path.join(location, "SerialCom_Failures.txt"), 'a') as fw:
						fw.write("\n")
						fw.write(f"Fails are from following file {(os.path.join(root, file))}")
						fw.write("\n")
						for line in filer:
							if "bad master node" in line:
								fw.write(f"Bad Master Node error      {line}")
							if "failed to unprotect master node" in line:
								fw.write(f"Bad Master Node error      {line}")
							if "Kernel panic" in line:
								fw.write(f"Bad Master Node error - Kernel panic     {line}")
							c = UBIFS_corruption.search(line)
							if c:
								fw.write(f"Bad Master Node error - UBIFS_corruption     {line}")
							if "Fatal error on modem" in line:
								fw.write(f"Bad Master Node error - UBIFS_corruption     {line}")

if __name__ == "__main__":
	white_list_regex = ['nfs.service:.*status=15.TERM','vlansetup@usb0.service:.*status=15.TERM','vlansetup@usb0.service: Failed with result \'signal\'']
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
	COM_Port_Failures(filename)
	print("Successfully parsed")