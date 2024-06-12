import pandas as pd
import sys
import re,os
import numpy as np
import matplotlib.pyplot as plt

def convert_to_seconds(value):
    # Split the string into parts based on 'min' and 's'
    parts = value.split()
    # Initialize variables for minutes and seconds
    minutes = 0
    seconds = 0
    # Loop through the parts and add to minutes and seconds accordingly
    for part in parts:
        if "min" in part:
            minutes += int(part.replace("min", ""))
        elif "s" and "." in part:
            items = part.split(".")
            miliseconds = items[1].strip("s")
            seconds = int(items[0]) + int(miliseconds) / 1000
        elif "s" in part:
            seconds += int(part.replace("s", ""))
    # Convert the time to seconds
    total_seconds = minutes * 60 + seconds
    return total_seconds

def get_values_of_services():
    columns_not_wanted = ['Baseline_version','A7 Startup finished time','A35 Startup finished time']
    not_cv2x = ['Real Time Monitoring Started','Enda Signal Discovery Completed']
    # cv2x stabiline
    for item in columns_not_wanted:
        columns.remove(item)
    for item in columns:
        service_values = []
        raw_values = [x for x in cv2x_stabi[f'{item}']]
        regex_values = r'((\d+).(\d+))sec'
        for line in raw_values:
            a = re.search(regex_values, line)
            if a:
                service_values.append(float(a.group(1)))
        data = np.array(service_values)
        plt.ylabel('Values in Seconds')
        plt.xlabel(item + ' CV2X_stabiline')
        plt.grid(True)
        plt.plot(data, 'b')
        plt.savefig(f'{destination}\{item}-CV2X_stabiline.jpeg')
        plt.close()
    # cv2x mainline
    for item in columns:
        service_values = []
        raw_values = [x for x in cv2x_master[f'{item}']]
        regex_values = r'((\d+).(\d+))sec'
        for line in raw_values:
            a = re.search(regex_values, line)
            if a:
                service_values.append(float(a.group(1)))
        data = np.array(service_values)
        plt.ylabel('Values in Seconds')
        plt.xlabel(item + ' CV2X_master')
        plt.grid(True)
        plt.plot(data, 'b')
        plt.savefig(f'{destination}\{item}-CV2X_master.jpeg')
        plt.close()
    #stabi
    for item in not_cv2x:
        columns.remove(item)
    for item in columns:
        service_values = []
        raw_values = [x for x in stabi[f'{item}']]
        regex_values = r'((\d+).(\d+))sec'
        for line in raw_values:
            a = re.search(regex_values,line)
            if a:
                service_values.append(float(a.group(1)))
        data = np.array(service_values)
        plt.ylabel('Values in Seconds')
        plt.xlabel(item+' Stabiline')
        plt.grid(True)
        plt.plot(data,'purple')
        plt.savefig(f'{destination}\{item}-Stabiline.jpeg')
        plt.close()
    #masterline
    for item in columns:
        service_values = []
        raw_values = [x for x in master[f'{item}']]
        regex_values = r'((\d+).(\d+))sec'
        for line in raw_values:
            a = re.search(regex_values, line)
            if a:
                service_values.append(float(a.group(1)))
        data = np.array(service_values)
        plt.ylabel('Values in Seconds')
        plt.xlabel(item + ' Masterline')
        plt.grid(True)
        plt.plot(data, 'r')
        plt.savefig(f'{destination}\{item}-Masterline.jpeg')
        plt.close()

def get_A7_A35_startup():
    #CV2x stabi
    for item in columns:
        if item == 'A7 Startup finished time':
            service_values = []
            raw_values = [x for x in cv2x_stabi[f'{item}']]
            for value in raw_values:
                if value != "Missing value":
                    service_values.append(float(convert_to_seconds(value)))
            data = np.array(service_values)
            plt.ylabel('Values in Seconds')
            plt.xlabel(item + ' CV2X_Stabiline')
            plt.grid(True)
            plt.plot(data, 'b')
            plt.savefig(f'{destination}\{item}-CV2X_Stabiline.jpeg')
            plt.close()
        elif item == 'A35 Startup finished time':
            service_values = []
            raw_values = [x for x in cv2x_stabi[f'{item}']]
            for value in raw_values:
                if value != "Missing value":
                    service_values.append(float(convert_to_seconds(value)))
            data = np.array(service_values)
            plt.ylabel('Values in Seconds')
            plt.xlabel(item + ' CV2X_Stabiline')
            plt.grid(True)
            plt.plot(data, 'b')
            plt.savefig(f'{destination}\{item}-CV2X_Stabiline.jpeg')
            plt.close()
        # CV2x master
        for item in columns:
            if item == 'A7 Startup finished time':
                service_values = []
                raw_values = [x for x in cv2x_master[f'{item}']]
                for value in raw_values:
                    if value != "Missing value":
                        service_values.append(float(convert_to_seconds(value)))
                data = np.array(service_values)
                plt.ylabel('Values in Seconds')
                plt.xlabel(item + ' CV2X_Mainline')
                plt.grid(True)
                plt.plot(data, 'b')
                plt.savefig(f'{destination}\{item}-CV2X_Mainline.jpeg')
                plt.close()
            elif item == 'A35 Startup finished time':
                service_values = []
                raw_values = [x for x in cv2x_master[f'{item}']]
                for value in raw_values:
                    if value != "Missing value":
                        service_values.append(float(convert_to_seconds(value)))
                data = np.array(service_values)
                plt.ylabel('Values in Seconds')
                plt.xlabel(item + ' CV2X_Mainline')
                plt.grid(True)
                plt.plot(data, 'b')
                plt.savefig(f'{destination}\{item}-CV2X_Mainline.jpeg')
                plt.close()
    #stabi
    for item in columns:
        if item == 'A7 Startup finished time':
            service_values = []
            raw_values = [x for x in stabi[f'{item}']]
            for value in raw_values:
                if value != "Missing value":
                    service_values.append(float(convert_to_seconds(value)))
            data = np.array(service_values)
            plt.ylabel('Values in Seconds')
            plt.xlabel(item + ' Stabiline')
            plt.grid(True)
            plt.plot(data, 'purple')
            plt.savefig(f'{destination}\{item}-Stabiline.jpeg')
            plt.close()
        elif item == 'A35 Startup finished time':
            service_values = []
            raw_values = [x for x in stabi[f'{item}']]
            for value in raw_values:
                if value != "Missing value":
                    service_values.append(float(convert_to_seconds(value)))
            data = np.array(service_values)
            plt.ylabel('Values in Seconds')
            plt.xlabel(item + ' Stabiline')
            plt.grid(True)
            plt.plot(data, 'purple')
            plt.savefig(f'{destination}\{item}-Stabiline.jpeg')
            plt.close()
        #Masterline
        for item in columns:
            if item == 'A7 Startup finished time':
                service_values = []
                raw_values = [x for x in master[f'{item}']]
                for value in raw_values:
                    if value != "Missing value":
                        service_values.append(float(convert_to_seconds(value)))
                data = np.array(service_values)
                plt.ylabel('Values in Seconds')
                plt.xlabel(item + ' Masterline')
                plt.grid(True)
                plt.plot(data, 'r')
                plt.savefig(f'{destination}\{item}-Masterline.jpeg')
                plt.close()
            elif item == 'A35 Startup finished time':
                service_values = []
                raw_values = [x for x in master[f'{item}']]
                for value in raw_values:
                    if value != "Missing value":
                        service_values.append(float(convert_to_seconds(value)))
                data = np.array(service_values)
                plt.ylabel('Values in Seconds')
                plt.xlabel(item + ' Masterline')
                plt.grid(True)
                plt.plot(data, 'r')
                plt.savefig(f'{destination}\{item}-Masterline.jpeg')
                plt.close()

def create_directory(destination):
    directory = "Services_Plot"
    if os.path.exists(os.path.join(destination,directory)):
        print(f"Directory {directory} already exists ,files will be saved in existing folder !")
        pass
    else:
        print(f"Directory {directory} does not exists exists , folder will be created and files will be saved in existing folder !")
        os.mkdir(os.path.join(destination,directory))
    return os.path.join(destination,directory)

if __name__ == '__main__':
    excel = sys.argv[1] #enter here the location of the KPI_Excel_File
    atp_tc_path = sys.argv[2] #enter here the location where you want the plots to be saved
    destination = create_directory(atp_tc_path)
    df = pd.read_excel(excel, sheet_name='KPI')
    columns = df.columns.to_list()
    stabi = df[(df['Baseline_version'].str.contains('LE21-D3-18.') | df['Baseline_version'].str.contains('LE21-18.') | df['Baseline_version'].str.contains('LE21-20.')) & (df['Baseline_version'].str.contains('-CV2X') == False)]
    master = df[(df['Baseline_version'].str.contains('LE21-21.')) & (df['Baseline_version'].str.contains('-CV2X') == False)]
    cv2x_stabi = df[(df['Baseline_version'].str.contains('LE21-20.')) & (df['Baseline_version'].str.contains('-CV2X') == True)]
    cv2x_master = df[(df['Baseline_version'].str.contains('LE21-21.')) & (df['Baseline_version'].str.contains('-CV2X') == True)]
    get_A7_A35_startup()
    get_values_of_services()
    print("Script completed successfully!")