import sys,re
from convert_dlt import decode_dlt_buffered_reader
import pandas as pd
import matplotlib.pyplot as plt
import os,optparse
from collections import defaultdict
import time,multiprocessing

parser = optparse.OptionParser()
parser.add_option('-p', '--path', action="store", dest="path", help="Location to your dlt files")
parser.add_option('-d', '--destination', action= "store", dest= "destination", help= "Location to save the Plot" )
options, args = parser.parse_args()

path = str(options.path)
destination = str(options.destination)

def logs_for_parse(path):
    filelist = [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(".dlt")]
    if len(filelist) == 0:
        print("No valid Dlt files for parsing were found for '{}' ! check script arguments and file naming ! ")
        sys.exit()
    else:
        print("Found {} valid Dlt files for parsing".format(len(filelist)))
    return filelist[0]


def get_ram_values_dictionary(filename):
    S = set() #Set item for all applications in order to avoid duplicates
    D = defaultdict(list) # Dictionary with all items key:value as list
    with open(filename, "rb") as f:
        try:
            decodeddata = decode_dlt_buffered_reader(f)
        except:
            return []
        result = []
        for decodedline in decodeddata:
            if (len(decodedline['PayLoad']) > 0) and isinstance(decodedline['PayLoad'], list):
                try:
                    if 'TOPR' in decodedline['PayLoad'][0]:
                        result.append((decodedline['PayLoad'][0].split('TOPR')[1].strip("\\n';")))
                    if  'TOPR' in decodedline['PayLoad'][0]:
                        time_values.append((decodedline['Date']))
                except : pass
        for x in result:
            ram_sec = x.split(';')
            for y in ram_sec:
                match = re.search(r'\d+,\d+,(\d+),\d+,\(([a-zA-Z-_.\d]+)\)', y)
                if match:
                    value, key = match.group(1),match.group(2)
                    if key not in S:
                        S.add(key)
                        D[key].append(int(value))
                    elif key in S:
                        D[key].append(int(value))
        # return D
        #new piece of code
        # Calculate the running average for each key
        running_average = {}
        for key, values in D.items():
            cumulative_average = []  # To store the running average for the key
            total = 0
            count = 0
            for value in values:
                total += value
                count += 1
                average = total / count
                cumulative_average.append(average)
            running_average[key] = cumulative_average
        for key, averages in running_average.items():
            if len(averages) < 30:
                continue  # Skip if there are not enough data points for a comparison
            initial_average = max(averages[0:30])
            final_average = averages[-1]
            if final_average > initial_average:
                try:
                    percent_increase = ((final_average - initial_average) / initial_average) * 100
                    if percent_increase >= 10:
                        print(f"Application {key} has a {percent_increase:.2f}% increase in running average.")
                except ZeroDivisionError as ex:
                    print(f"Exception occured as {ex} !")
        return running_average

def average(dictionar):
    #Prints average values for each application from a dictionary
    df_avg = {}
    for key, value in dictionar.items():
        if key != 'TIME':
            df_avg[key] = sum(value)/len(value)
    return df_avg

def return_time_values(list_with_datetime):
    strings = []
    for dt in list_with_datetime:
        string = dt.strftime("%Y-%m-%d %H:%M:%S")
        strings.append(string.split(" ")[1])
    return strings

def maximum_val(dict):
    df_max = {}
    for key, value in dict.items():
        if key != 'TIME':
            df_max[key] = max(value)
    return df_max

def first_value(dict):
    df_first = {}
    for key, value in dict.items():
        if key != 'TIME':
            df_first[key] = value[0]
    return df_first

def memory_leak(first_values, maximum_values):
    increase = {}
    for key in first_values.keys():
        if maximum_values[key] > first_values[key]:
            if int(first_values[key]) != 0:  # some values can have a 0 as result
                increase[key] = str(round(((maximum_values[key] - first_values[key]) / first_values[key]) * 100, 2)) + "%"
    if len(increase) != 0:
        print("Successfully verified for memory leaks!")
    return increase

def excel_report(all_values, avg_values, max_values, increase):
    all_values['TIME'] = return_time_values(time_values)
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in all_values.items()]))
    df = df.set_index('TIME')
    df_avg = pd.DataFrame(avg_values.items())
    df_max = pd.DataFrame(max_values.items())
    df_increase = pd.DataFrame(increase.items())
    df_avg.rename(columns = { 0 : "App name", 1 : "Average ram" }, inplace= True)
    df_max.rename(columns = { 0 : "App name", 1 : "Maximum ram" }, inplace= True)
    df_increase.rename(columns = { 0 : "App name", 1 : "Increase(in %)" }, inplace= True)
    writer = pd.ExcelWriter("{}\\Ram overview.xlsx".format(destination), engine='xlsxwriter')
    frames = {'Full overview': df, 'Average values': df_avg,
              'Maximum values': df_max, 'Increase': df_increase}
    for sheet, frame in frames.items():
        frame.to_excel(writer, sheet_name=sheet)
    writer.close()
    print("Successfully created Excel File")

def plot_figures(dictionar):
    for app_name, ram_values in dictionar.items():
        plt.plot(ram_values,label=app_name+" " + "service")
        plt.title("RAM Leaks - RAM Used over time")
        plt.grid(axis='y', alpha=0.75)
        plt.legend(loc='upper right')
        plt.xlabel('Number of measurements in ~6 hours of test')
        plt.ylabel('RAM Consumption in Kb')
        plt.savefig(destination + "/"f"Plot for {app_name} service.jpg", dpi=150)
        plt.close()
    print("Plotting of all figures done !")

if __name__ == "__main__":
    print("Parsing files ")
    start = time.time()
    time_values = []
    log_to_be_parsed = logs_for_parse(path)
    all_values_dict = get_ram_values_dictionary(log_to_be_parsed)
    increase = memory_leak(first_value(all_values_dict), maximum_val(all_values_dict))
    excel_report(all_values_dict,average(all_values_dict),maximum_val(all_values_dict),increase)
    plot_figures(all_values_dict)
    end = time.time()
    total_time = end - start
    print("\n" + f"Script executed in {str(total_time)}")