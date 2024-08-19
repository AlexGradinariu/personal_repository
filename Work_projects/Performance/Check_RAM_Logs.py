''' check_soc_ram_cpu.py
' This Python script gets SoC RAM and CPU measurements from logs file
'
' Creation Date: 2018-12-13
' Last Updated: 2019-05-17
' Author: Christopher Haccius (christopher.haccius@continental-corporation.com)
' Copyright: 2019 Continental Automotive GmbH
'''

from __future__ import print_function
import os, sys

import optparse
from datetime import datetime


def avg(arr: list):
    return sum(arr) / len(arr)


def parse_log_file(infile, resource):
    """
    Parsing files to find the RAM log files sitting in the logs directory
    """
    RAM = []
    RAMFREE = []
    CPU = []
    SIRQ = []
    B2B = []
    B2C = []
    mytime = datetime.strptime('1970-01-01/12:12:12', '%Y-%m-%d/%H:%M:%S')
    tmptime = mytime
    for line in infile:
        try:
            linetime = datetime.strptime(line.split(' ')[0], '%Y-%m-%d/%H:%M:%S')
            if abs((linetime - tmptime).total_seconds()) > 5:
                mytime = linetime
                tmptime = linetime
            else:
                tmptime = linetime
        except Exception as e:
            linetime = None
            # print(line.split(' ')[0])
            # print(e)
        try:
            if 'TOPR System wide memory information:' in line:
                RAM.append(float(line.split('RAM: ')[1].split(' MiB')[0]) - float(line.split('MiB (')[1].split(' free')[0]))
                RAM.append(line.split('MiB (')[1].split(' free')[0] + "MiB free")
            if 'TOPC: CPU: ' in line:
                CPU.append(100.0 - float(line.split('nic ')[1].split('% idle')[0]))
                SIRQ.append(float(line.split(' ')[-2].strip("%")))
            if 'handleSignal:Connected B2B' in line and linetime:
                B2B.append(abs((linetime - mytime).total_seconds()))
            if 'handleSignal:B2C Connected' in line and linetime:
                B2C.append(abs((linetime - mytime).total_seconds()))
        except:pass
    if resource == 'RAM':
        return RAM
    if resource == 'CPU':
        return CPU
    if resource == 'B2B':
        return B2B
    if resource == 'B2C':
        return B2C
    if resource == 'SIRQ':
        return SIRQ
    else:
        return None




def output(filename, resource, analytics):
    # parser.add_option('-r', '--resource',
    #     action="store", dest="resource",
    #     help="resource to be checked, options are 'RAM', 'CPU', 'B2B', 'B2C' (default: RAM)", default="RAM")
    # parser.add_option('-a', '--analytics',
    #     action="store", dest="analytics",
    #     help="analytics to be applied, options are 'AVG', 'MAX, 'MIN' (default: MAX)", default="MAX")

    value = parse_log_file(open(filename, 'r', encoding='latin-1'), resource)
    if resource == 'RAM':
        if analytics == 'MAX':
            if value:
                max_ram = [float(x) for x in value if x is not None and "MiB free" not in str(x)]
                return "%.2f" % (max(max_ram) * 1.048576)
        elif analytics == 'MIN':
            if value:
                min_ram = [float(x) for x in value if x is not None and "MiB free" not in str(x)]
                return "%.2f" % (min(min_ram) * 1.048576)
        elif analytics == 'AVG':
            if value:
                avg_consumption = [float(x) for x in value if x is not None and "MiB free" not in str(x)]
                return "%.2f" % (avg(avg_consumption) * 1.048576)
        elif analytics == 'AVGFREE':
            if value:
                avg_free = [float(x.replace("MiB free", "")) for x in value if x is not None and "MiB free" in str(x)]
                return "%.2f" % (avg(avg_free))
    elif resource == 'CPU':
        if analytics == 'MAX':
            if value:
                return "%.2f" % max(value)
        elif analytics == 'MIN':
            if value:
                return "%.2f" % min(value)
        elif analytics == 'AVG':
            if value:
                return "%.2f" % avg(value)
    elif resource == 'SIRQ':
        if analytics == 'MAX':
            if value:
                return "%.2f" % max(value)
        elif analytics == 'MIN':
            if value:
                return "%.2f" % min(value)
        elif analytics == 'AVG':
            if value:
                return "%.2f" % avg(value)
    elif resource == 'B2B':
        if analytics == 'MAX':
            print("%.2f sec" % max(value))
        elif analytics == 'MIN':
            print("%.2f sec" % min(value))
        elif analytics == 'AVG':
            print("%.2f sec" % avg(value))
    elif resource == 'B2C':
        if analytics == 'MAX':
            print("%.2f sec" % max(value))
        elif analytics == 'MIN':
            print("%.2f sec" % min(value))
        elif analytics == 'AVG':
            print("%.2f sec" % avg(value))


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file', action="store", dest="filename",
                      help="filename of messages.X file (default: messages)")
    options, args = parser.parse_args()

    filenameList = []
    rss = ["RAM", "CPU", "SIRQ"]
    ann = ["MAX", "AVG", "MIN", "AVGFREE"]
    avg_ram = []
    avg_cpu = []
    avg_sirq =[]
    max_ram = []
    max_sirq =[]
    max_cpu = []
    min_ram = []
    min_cpu = []
    min_sirq = []
    avg_free_ram = []

    if options.filename:
        for root, dirs, files in os.walk(options.filename):
            for file in files:
                if file.startswith("messages"):
                    filenameList.append(os.path.join(root, file))

        print(filenameList)
        if filenameList:
            for x in rss:
                for y in ann:
                    for filename in filenameList:
                        if x == "RAM" and y == "MAX":
                            max_ram.append(output(filename, x, y))
                        elif x == "RAM" and y == "AVG":
                            avg_ram.append(output(filename, x, y))
                        elif x == "CPU" and y == "MAX":
                            max_cpu.append(output(filename, x, y))
                        elif x == "CPU" and y == "AVG":
                            avg_cpu.append(output(filename, x, y))
                        elif x == "CPU" and y == "MIN":
                            min_cpu.append(output(filename, x, y))
                        elif x == "RAM" and y == "MIN":
                            min_ram.append(output(filename, x, y))
                        elif x == "RAM" and y == "AVGFREE":
                            avg_free_ram.append(output(filename, x, y))
                        elif x == "SIRQ" and y == "MAX":
                            max_sirq.append(output(filename, x, y))
                        elif x == "SIRQ" and y == "AVG":
                            avg_sirq.append(output(filename, x, y))
                        elif x == "SIRQ" and y == "MIN":
                            min_sirq.append(output(filename, x, y))

        max_ram = [float(x) for x in max_ram if x != None]
        avg_ram = [float(x) for x in avg_ram if x != None]
        min_ram = [float(x) for x in min_ram if x != None]
        max_cpu = [float(x) for x in max_cpu if x != None]
        avg_cpu = [float(x) for x in avg_cpu if x != None]
        min_cpu = [float(x) for x in min_cpu if x != None]
        avg_free_ram = [float(x) for x in avg_free_ram if x != None]
        max_sirq = [float(x) for x in max_sirq if x != None]
        avg_sirq = [float(x) for x in avg_sirq if x != None]
        min_sirq = [float(x) for x in min_sirq if x != None]

        print("RAM Measurements")
        try:
            if len(avg_ram) and len(avg_free_ram) and len(min_ram) and len(max_ram):
                print("Average ram consumption was: " + "%.2f MByte" % avg(avg_ram))
                print("Average free ram memory was: " + "%.2f MByte" % avg(avg_free_ram))
                print("Maximum ram consumption was: " + "%.2f MByte" % max(max_ram))
                print("Minimum ram consumption was: " + "%.2f MByte" % min(min_ram))
            else :
                print("No valid RAM traces found ! ")
        except Exception as e:
            print(f"Exception occured on RAM measurements as : {e} !")

        print("CPU Measurements")
        print("Maximum CPU consumption was: " + "%.2f%%" % max(max_cpu))
        print("Average CPU consumption was: " + "%.2f%%" % avg(avg_cpu))
        print("Minimum CPU consumption was: " + "%.2f%%" % min(min_cpu))
        print("CPU SIRQ Measurements")
        print("Maximum SIRQ CPU consumption was: " + "%.2f%%" % max(max_sirq))
        print("Average SIRQ CPU consumption was: " + "%.2f%%" % avg(avg_sirq))
        print("Minimum SIRQ CPU consumption was: " + "%.2f%%" % min(min_sirq))

    else:
        sys.exit(15)
