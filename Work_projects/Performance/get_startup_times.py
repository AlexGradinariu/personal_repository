'''
' get_startup_times.py
' script to extract startup times from messages files
'
' Creation Date: 2019-06-14
' Last Updated: 2019-06-14
' Contact Authot: Christopher Haccius
' EMail: christopher.haccius@continental-corporation.com
' Copyright: 2019 Continental Automotive GmbH
' Edited: Gradinariu Alexandru
'''


import optparse
import json, os
import re
import statistics


def parse_message_file(filename, measurements, tests):
    """
    Iterate over message file, keep track of kernel time
    and check for lines in JSON File
    """
    ktime = 0.0
    regex = "(.+? ){4}(\d)" #regex for lines without systemd[1]: Started
    regex1 = "(\d+.\d+)\ssystemd" #regex for lines with systemd[1]: Started
    mfile = open(filename, 'r', encoding="latin-1")
    print("\nMeasurements are from: {}".format(filename))
    for line in mfile:
        for stest in tests:
            if tests[stest]['line'] in line:
                if "systemd" in line:
                    try:
                        l=re.search(regex1,line.lstrip(" "))
                        ktime=float(l.group(1))
                    except:
                        print("Exception at snatching timestamp! Moving on..")
                        pass
                    #print("%8.2fsec: %s" % (ktime, tests[stest]['name']))
                    if tests[stest]['name'] in measurements:
                        measurements[tests[stest]['name']].append(ktime)
                        print(line, ktime)
                    else:
                        measurements[tests[stest]['name']] = [ktime]
                else:
                    try:
                        l = re.search(regex, line.lstrip(" "))
                        ktime = float(l.group(1))
                        print(line, ktime)
                    except:
                        print("Exception at snatching timestamp! Moving on..")
                        pass
                        # print("%8.2fsec: %s" % (ktime, tests[stest]['name']))
                    if tests[stest]['name'] in measurements:
                        measurements[tests[stest]['name']].append(ktime)
                    else:
                        measurements[tests[stest]['name']] = [ktime]
    mfile.close()
    return measurements
    
def mean_without_outliers(arr):
    for x in range(1, int(len(arr)/3)):
        mean = sum(arr)/len(arr)
        arr.sort()
        if mean-arr[0] > arr[len(arr)-1]-mean:
            arr = arr[1:len(arr)-1]
        else:
            arr = arr[0:len(arr)-2]
    return sum(arr)/len(arr)
    
def parse_and_publish(message_files, version):
    measurements = {}
    
    tests = None
    with open('startup_config.json') as json_file:
        tests = json.load(json_file)
    
    for message_file in message_files:
        measurements = parse_message_file(message_file, measurements, tests)
        
    filename = 'startup_kpis_' + version + '.csv'
    csv_file = open(filename, "w")
    csv_file.write("Label,"+version+"\n")
    for name, measures in measurements.items():  # code for Python3
        csv_file.write("KPI,%s,%.2f\n" % (name, mean_without_outliers(measures)))
        # print("KPI,%s,%.2f\n" % (name, mean_without_outliers(measures)))
    csv_file.close()
    return filename
        
def parse_and_print():
    measurements = {}

    parser = optparse.OptionParser()
    parser.add_option('-f', '--file',
        action="store", dest="filename",
        help="filename of bootchart file (default: messages)", default="messages")
    parser.add_option('-c', '--config',
       action="store", dest="config",
        help="filename of config file (default: startup_config.json)", default="startup_config.json")

    options, args = parser.parse_args()
    filenames = options.filename.strip('"')
    filenameList = list()
    for root, dirs, files in os.walk(filenames):
        for file in files:
            if file.startswith("messages"):
                filenameList.append(os.path.join(root,file))

    #filenameList = filenames.split(",")
    tests = None
    with open('startup_config.json') as json_file:
        tests = json.load(json_file)
    
    for filename in filenameList:
        measurements = parse_message_file(filename, measurements, tests)

    print("\n\n#### Average Measurements####")
    #for name, measures in measurements.iteritems():  # code for Python2
    for name, measures in measurements.items():  # code for Python3
        print("%8.2fsec: %s" % (mean_without_outliers(measures), name))
    print("\n\n#### Maximum Measurements####")
    #for name, measures in measurements.iteritems():  # code for Python2
    for name, measures in measurements.items():  # code for Python3
        print("%8.2fsec: %s" % (max(measures), name))
    print("\n\n#### Minimum Measurements####")
    # for name, measures in measurements.iteritems():  # code for Python2
    for name, measures in measurements.items():  # code for Python3
        print("%8.2fsec: %s" % (min(measures), name))
    print("\n\n#### Median Measurements####")
    for name, measures in measurements.items():
        print("%8.2fsec: %s" % (statistics.median(measures), name))
    #add ecall values in a list so they can be parse in the bellow function
    #for ecall_value in measurements['ECall Available']:
        #Ecall_measuremets.append(ecall_value)

def check_deviation(lst):
    print("\n\n####Search for ECall KPI Startup Deviations####")
    lst.sort()
    if (lst[-1] - lst[0]) > 1.5:
        print(f"Ecall Deviation greater that 1.5 seconds found between Max and Min startup values {lst[-1]}s and {lst[0]}s -> {round((lst[-1] - lst[0]),2)}s")
    else :
        print("No deviation found between startup values bigger than 1.5 seconds !")
    if lst[-1] > 42:
        print(f"Ecall KPI of 42s startup time exceeded !")
    else :
        print("Ecall KPI startup time of 42s not exceeded !")


if __name__ == "__main__":
    Ecall_measuremets = []
    parse_and_print()
    #check_deviation(Ecall_measuremets)