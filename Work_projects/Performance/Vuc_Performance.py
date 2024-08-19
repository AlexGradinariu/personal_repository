import re,optparse,sys,os


def parse_log_file(filename,vuc_port):
    CPU = []
    Os_Error = []

    cpu_regex = "CurrentCpuLoad\s(\d+)"
    # os_errorregex = "OS\sErrors\sincreased\sto\s(\d+)"

    for root, dirs, files in os.walk(filename):
        for file in files:
            if vuc_port in file:
                with open(os.path.join(root, file),"r",encoding="utf8") as file:
                    for line in file:
                        try:
                            cpu=re.search(cpu_regex,line.lstrip())
                            # oserr=re.search(os_errorregex,line.lstrip())
                            if cpu != None:
                                CPU.append(float(cpu.group(1)))
                            # if oserr !=None:
                            #     Os_Error.append(float(oserr.group(1)))
                        except Exception as e:
                            print(e)
                average_cpu_load = (sum(CPU)/len(CPU))
                # number_of_errors = Os_Error[-1]-Os_Error[0]
                print(f"Maximum M4_CPU_Load is: {max(CPU)}% ")
                print(f"Average M4_CPU_Load is: {round(average_cpu_load,2)}%")
                print(f"Minimum M4_CPU_Load is: {min(CPU)}% ")
                # print(f"Total Number of OS Errors is: {round(number_of_errors)}")
                print("Successfully parsed!")



if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file', action="store", dest="filename", help="folder with txt file")
    parser.add_option('-p', '--vuc_port', action="store", dest="vuc_port", help="VUC_COM_PORt")
    options, args = parser.parse_args()
    filename = options.filename
    vuc_port = options.vuc_port

    parse_log_file(filename,vuc_port)
    if not os.path.exists(filename):
        print("Location is invalid!")
        sys.exit()