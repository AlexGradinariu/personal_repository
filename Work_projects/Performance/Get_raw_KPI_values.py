import os
import re
import json
import sys
import pandas as pd
import shutil


def get_all_messages_files(path):
    parent_dir = os.path.dirname(path)
    filelist = [os.path.join(root, file) for root, dirs, files in os.walk(parent_dir) for file in files if file.startswith("messages")]
    return filelist


def parse_message_file(filename,json_kpi_traces): #receives a list of messages files in order to parse them
    raw_value = {}
    """
    Iterate over message file, keep track of kernel time
    and check for lines in JSON File
    """
    regex_without_systemd = "(.+? ){4}(\d)" #regex_without_systemd for lines without systemd[1]: Started
    with_systemd_regex = "(\d+.\d+)\ssystemd" #regex_without_systemd for lines with systemd[1]: Started
    with open(json_kpi_traces) as json_file:
        tests = json.load(json_file)
        service_name = [test['name'] for test in tests.values()]
        service_trace = [test['line'] for test in tests.values()]
    for file in filename:
        with open(file, 'r', encoding="latin-1") as mfile:
            print("\nMeasurements are from: {}".format(file))
            for line in mfile:
                for trace, name in zip(service_trace, service_name):
                    if trace in line and "systemd" in line:
                        try:
                            value = re.search(with_systemd_regex, line.lstrip(" "))
                            if name in raw_value:
                                raw_value[name].append(value.group(1))
                            else:
                                    raw_value[name] = [value.group(1)]
                        except Exception as e:
                            print("Exception at snatching timestamp:", e)
                    else:
                        if trace in line:
                            try:
                                value = re.search(regex_without_systemd, line.lstrip(" "))
                                if name in raw_value:
                                    raw_value[name].append(value.group(1))
                                else:
                                    raw_value[name] = [value.group(1)]
                            except Exception as e:
                                print(f"Exception {e} at snatching timestamp! Moving on..")
    return raw_value

def get_local_values_for_project():
    nad_folder_path = r"D:\DRT16_CT\il_update\nad"
    test_bench = os.getenv("hostname")
    config_file = [files for files in os.listdir(nad_folder_path) if "le21_config.txt" in files]
    filename = os.path.join(nad_folder_path, config_file[0])
    if filename:
        print(f'File {config_file} was found ,continuing... ')
        with open(filename,encoding='utf-8') as f:
            for line in f:
                if "myDate" in line:
                    _, value = line.strip().split("=")
                    date = "-".join([value[1:5], value[5:7], value[7:9]])
                    hour = ":".join([value[10:12], value[12:14], value[14:16]])
                if "BANNER_ARG_1" in line :
                    _, value = line.strip().split("=")
                    baseline = value.strip(' " ')
            return test_bench, date, hour, baseline
    else:
        print("Config txt file not found")
        return test_bench, 'date_unavailable', "timestamp_unavailable", "baseline_unavailable"

get_local_values_for_project()


def copy_excel_file(location_where_to_copy,path_to_excel_file):

    excel_name = "DRT15_Baseline_RAW_KPI_values.xlsx"
    excel_full_path = os.path.join(path_to_excel_file, excel_name)
    print(excel_full_path)
    if os.path.exists(excel_full_path):
        try:
            shutil.copy(excel_full_path,location_where_to_copy)
            print("Successfully copied")
        except OSError as e:
            print(f"Error copying due to -> {e}")
    else:
        print("Destination file not found")

def create_data_frame(data_kpi_dict, date, hour, baseline, testbench, excel_location):
    excel_name = "DRT15_Baseline_RAW_KPI_values.xlsx"
    file_path = os.path.join(excel_location, excel_name)
    if os.path.isfile(file_path):
        print(f"Excel {excel_name} existing,continuing by adding new data frame... ")
        initial_df = pd.read_excel(file_path,sheet_name="KPI")
        df_kpi = pd.DataFrame(data_kpi_dict.items())
        service_name = "Service Name"
        df_kpi.rename(columns={0: service_name, 1: "Values"}, inplace=True)
        df_kpi['Date'] = [date] * len(df_kpi[service_name])
        df_kpi['Hour'] = [hour] * len(df_kpi[service_name])
        df_kpi['Baseline'] = [baseline] * len(df_kpi[service_name])
        df_kpi['Test_script_version'] = ["v1.0"] * len(df_kpi[service_name])
        df_kpi["Test Bench"] = [testbench] * len(df_kpi[service_name])
        df_kpi['Tags'] = ["-"] * len(df_kpi["Service Name"])
        df_kpi = df_kpi[['Date', 'Hour', 'Baseline', service_name, 'Values', "Test Bench", 'Test_script_version', 'Tags']]
        concatenated_df = pd.concat([initial_df, df_kpi], ignore_index=True)
        concatenated_df.to_excel(file_path,sheet_name="KPI", index=False)

    else:
        print("Excel file for KPIs values not existing, creating Excel file and append new dataframe")
        df_kpi = pd.DataFrame(data_kpi_dict.items())
        service_name = "Service Name"
        df_kpi.rename(columns={0: service_name, 1: "Values"}, inplace=True)
        df_kpi['Date'] = [date] * len(df_kpi[service_name])
        df_kpi['Hour'] = [hour] * len(df_kpi[service_name])
        df_kpi['Baseline'] = [baseline] * len(df_kpi[service_name])
        df_kpi['Test_script_version'] = ["v1.0"] * len(df_kpi[service_name])
        df_kpi["Test Bench"] = [testbench] * len(df_kpi[service_name])
        df_kpi['Tags'] = ["-"] * len(df_kpi["Service Name"])
        df_kpi = df_kpi[['Date', 'Hour', 'Baseline', service_name, 'Values', "Test Bench", 'Test_script_version', 'Tags']]
        df_kpi.to_excel(file_path,sheet_name="KPI",index=False)

if __name__ == "__main__":
    list_of_accepted_pcs = ['IALN727W', 'IADO795W', 'IADO794W', 'IADL844W', 'IAD8544W', 'IADK612W', 'IADK611W',
                            'IALN227W', 'IALV775W']
    if os.getenv('HOSTNAME').upper() in [item.upper() for item in list_of_accepted_pcs]:
        print(f"{os.getenv('HOSTNAME').upper()} is an SyI Test Bench, continuing script...")
        path_from_test_bench = sys.argv[1]
        json_path = sys.argv[2]
        path_of_excel_file = sys.argv[3]
        files = get_all_messages_files(path_from_test_bench)
        data_dictionary = parse_message_file(files, json_path)
        test_bench, date, hour ,baseline = get_local_values_for_project()
        copy_excel_file(path_from_test_bench, path_of_excel_file)
        create_data_frame(data_dictionary,date,hour,baseline,test_bench,path_of_excel_file)
        print("Script completed successfully")
    else:print(f"{os.getenv('HOSTNAME').upper()} is not an SyI Test Bench, continuing script...")
