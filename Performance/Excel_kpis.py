import os,shutil
import re,sys
import pandas as pd
import optparse,statistics

#dataframe A7 Node
A7_kpi_dict = {"A7 Startup finished time":"",
                "Max mbecall.service":"",
                "Median mbecall.service":"",
                "Min mbecall.service":"",
               "AVG diag-mgr.service":"",
               "AVG APN2.B2B connected":"",
               "AVG APN3.B2C connected":"",
               "Enda Signal Discovery Completed":"",
               "Real Time Monitoring Started":""}
A7_cpu_metrics = {"AVG RAM":"",
                "AVG FREE RAM":"",
                "Max RAM":"",
                "MAX CPU":"",
                "AVG CPU":"",
                "MAX SIRQ CPU":"",
                "AVG SIRQ CPU":""}
A35_kpi_dict = {"A35 Startup finished time":"",
                "AVG Remote Diagnostics Available":"",
                "SWL-App":""}
A35_cpu_metrics = {"AVG RAM":"",
                   "AVG FREE RAM":"",
                   "Max RAM":"",
                   "MAX CPU":"",
                   "AVG CPU":""}
VUC_Metrics = {"Maximum M4_CPU_Load":"",
               "Average M4_CPU_Load":"",
               "Minimum M4_CPU_Load":""}
#parser options
parser = optparse.OptionParser()
parser.add_option('-f', '--file',action="store", dest="filename",help="filename of messages file (default: .txt files)")
parser.add_option('-d', '--dest',action="store", dest="destination",help="destination of output Excel file")
parser.add_option('-m', '--max',action="store", dest="vuc_max",help="VUC_Max_CPU_Value")
parser.add_option('-l', '--min',action="store", dest="vuc_min",help="VUC_Min_CPU_Value")
parser.add_option('-a', '--average',action="store", dest="vuc_average",help="VUC_Average_CPU_Value")
parser.add_option('-b', '--baseline',action="store", dest="baseline",help="baseline banner")
parser.add_option('-c', '--sharedrive',action="store", dest="sharedrive",help="Sharedrive location where excel will be stored")

options, args = parser.parse_args()
filename = options.filename
destination = options.destination
vuc_max=options.vuc_max
vuc_min=options.vuc_min
vuc_average=options.vuc_average
baseline = str(options.baseline).strip()
sharedrive = options.sharedrive

#function to replace empty values
def empty_to_value(d):
    # d = dict( [(k,v) for k,v in d.items() if len(v)>0])
    # for key, value in d.items():
    #     if len(value) == 0:
    #         d[value] = "missing value"
    # print(d)
    return({k: v or "Missing value" for k, v in d.items()})
def create_a7_service_kpi():
    ecall_values = []
    diag_values = []
    b2b_apn = []
    b2c_apn = []
    enda_values = []
    rtm_values = []
    a7_startup = re.compile("\(userspace\)\s=\s(.*)")
    # ecall = re.compile("\s\s\s\s(.*):\sECall\sAvailable")
    ecall = re.compile("\s((\d+).(\d+))\s(\d+)\sNAD\sECAL.*finalizeInitialization:waitVal:")
    diag = re.compile("((\d+).(\d+))\ssystemd.*Started DRT Software Diagnosis")
    b2b = re.compile("((\d+).(\d+))\s(\d+)\sNAD\sSUBM\s*.*rmnet_data0.*CONNECTED")
    b2c = re.compile("((\d+).(\d+))\s(\d+)\sNAD\sSUBM\s*.*rmnet_data1.*CONNECTED")
    enda = re.compile("((\d+).(\d+))\s(\d+)\sNAD\sElec\sElec")
    rtm = re.compile("((\d+).(\d+))\s(\d+)\sNAD\sRTM.*:main:start main loop")
    for root, dirs, files in os.walk(filename):
        for file in files:
            if file.endswith("NAD.txt"):
                with open(os.path.join(filename,file),"r", encoding="utf-8") as file1:
                    for x in file1:
                        #regex_for_values
                        f = a7_startup.search(x)
                        g = ecall.search(x)
                        h = diag.search(x)
                        i = b2b.search(x)
                        j = b2c.search(x)
                        k = enda.search(x)
                        l = rtm.search(x)
                        # add Ram values to dict
                        if f:
                            A7_kpi_dict["A7 Startup finished time"] = str(f.group(1))
                        elif g:
                            ecall_values.append(float(g.group(1)))
                        elif h:
                            diag_values.append(float(h.group(1)))
                        elif i:
                            b2b_apn.append(float(i.group(1)))
                        elif j:
                            b2c_apn.append(float(j.group(1)))
                        elif k:
                            enda_values.append(float(k.group(1)))
                        elif l:
                            rtm_values.append(float(l.group(1)))
    b2b_apn = [x for x in b2b_apn if x <= 150]
    b2c_apn = [x for x in b2c_apn if x <= 150]
    rtm_values = [x for x in rtm_values if x <= 200]
    try:
        if len(ecall_values) != 0:
            A7_kpi_dict["Max mbecall.service"] = str(round(max(ecall_values),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    try:
        if len(ecall_values) != 0:
            A7_kpi_dict["Median mbecall.service"] = str(round(statistics.median(ecall_values),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    try:
        if len(ecall_values) != 0:
            A7_kpi_dict["Min mbecall.service"] = str(round(min(ecall_values),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    try:
        if len(diag_values) != 0:
            A7_kpi_dict["AVG diag-mgr.service"] = str(round(statistics.mean(diag_values),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    try:
        if len(b2b_apn) != 0:
            A7_kpi_dict["AVG APN2.B2B connected"] = str(round(statistics.mean(b2b_apn),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    try:
        if len(b2c_apn) != 0:
            A7_kpi_dict["AVG APN3.B2C connected"] = str(round(statistics.mean(b2c_apn),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    try:
        if len(enda_values) != 0:
            A7_kpi_dict["Enda Signal Discovery Completed"] = str(round(statistics.mean(enda_values),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    try:
        if len(rtm_values) != 0:
            A7_kpi_dict["Real Time Monitoring Started"] = str(round(statistics.mean(rtm_values),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    return ecall_values,diag_values,b2b_apn,b2c_apn,enda_values,rtm_values

def create_a7_ram_cpu_kpi():
    avg_ram = re.compile("Average\sram\sconsumption\swas:\s(.*)")
    free_ram = re.compile("free\sram\smemory\swas:\s(.*)")
    max_ram = re.compile("Maximum\sram\sconsumption\swas:\s(.*)")
    max_cpu = re.compile("Maximum\sCPU\sconsumption\swas:\s(.*)")
    avg_cpu = re.compile("Average\sCPU\sconsumption\swas:\s(.*)")
    max_sirq_cpu = re.compile("Maximum SIRQ\sCPU\sconsumption\swas:\s(.*)")
    avg_sirq_cpu = re.compile("Average SIRQ\sCPU\sconsumption\swas:\s(.*)")
    for root, dirs, files in os.walk(filename):
        for file in files:
            if file.endswith("NAD.txt"):
                with open(os.path.join(filename,file),"r", encoding="utf-8") as file1:
                    for x in file1:
                        a = avg_ram.search(x)
                        b = free_ram.search(x)
                        c = max_ram.search(x)
                        d = max_cpu.search(x)
                        e = avg_cpu.search(x)
                        f = max_sirq_cpu.search(x)
                        g = avg_sirq_cpu.search(x)
                        if a :
                            A7_cpu_metrics["AVG RAM"]=str(a.group(1))
                        elif b:
                            A7_cpu_metrics["AVG FREE RAM"] = str(b.group(1))
                        elif c:
                            A7_cpu_metrics["Max RAM"] = str(c.group(1))
                        elif d:
                            A7_cpu_metrics["MAX CPU"] = str(d.group(1))
                        elif e:
                            A7_cpu_metrics["AVG CPU"] = str(e.group(1))
                        elif f:
                            A7_cpu_metrics["MAX SIRQ CPU"] =str(f.group(1))
                        elif g:
                            A7_cpu_metrics["AVG SIRQ CPU"] = str(g.group(1))
def create_a35_ram_cpu_kpi():
    avg_ram = re.compile("Average\sram\sconsumption\swas:\s(.*)")
    free_ram = re.compile("free\sram\smemory\swas:\s(.*)")
    max_ram = re.compile("Maximum\sram\sconsumption\swas:\s(.*)")
    max_cpu = re.compile("Maximum\sCPU\sconsumption\swas:\s(.*)")
    avg_cpu = re.compile("Average\sCPU\sconsumption\swas:\s(.*)")
    for root, dirs, files in os.walk(filename):
        for file in files:
            if file.endswith("IMX.txt"):
                with open(os.path.join(filename,file),"r", encoding="utf-8") as file1:
                    for x in file1:
                        a = avg_ram.search(x)
                        b = free_ram.search(x)
                        c = max_ram.search(x)
                        d = max_cpu.search(x)
                        e = avg_cpu.search(x)
                        if a :
                            A35_cpu_metrics["AVG RAM"]=str(a.group(1))
                        elif b:
                            A35_cpu_metrics["AVG FREE RAM"] = str(b.group(1))
                        elif c:
                            A35_cpu_metrics["Max RAM"] = str(c.group(1))
                        elif d:
                            A35_cpu_metrics["MAX CPU"] = str(d.group(1))
                        elif e:
                            A35_cpu_metrics["AVG CPU"] = str(e.group(1))
def create_a35_service_kpi():
    rem_diag = []
    swl_app = []
    a35_startup = re.compile("\(userspace\)\s=\s(.*)")
    rdiag = re.compile("((\d+).(\d+))\s(\d+)\sIMX.*DRT\sRemote\sDiagnosis\sApplication")
    swl=re.compile("((\d+).(\d+))\s(\d+)\sIMX\sSWLA")
    for root, dirs, files in os.walk(filename):
        for file in files:
            if file.endswith("IMX.txt"):
                with open(os.path.join(filename,file),"r", encoding="utf-8") as file1:
                    for x in file1:
                        #regex_for_values
                        f = a35_startup.search(x)
                        g = rdiag.search(x)
                        h = swl.search(x)
                        # add Ram values to dict
                        if f:
                            A35_kpi_dict["A35 Startup finished time"] = str(f.group(1))
                        elif g:
                            rem_diag.append(float(g.group(1)))
                        elif h:
                            swl_app.append(float(h.group(1)))
    swl_app = [x for x in swl_app if 70 <= x] # in order to exclude values that may be from LPM ,under 30 seconds that will break the average
    try:
        if len(rem_diag) != 0:
            A35_kpi_dict["AVG Remote Diagnostics Available"] = str(round(statistics.mean(rem_diag),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    try:
        if len(swl_app) != 0:
            A35_kpi_dict["SWL-App"] = str(round(statistics.mean(swl_app),2)) + "sec"
    except Exception as e:
        print(f"Exception occured as {e}")
    return rem_diag,swl_app

def create_vuc_kpi(vuc_max,vuc_min,vuc_average):
    if len(str(vuc_max)) != 0:
        VUC_Metrics["Maximum M4_CPU_Load"] = str(vuc_max)
    if len(str(vuc_average)) != 0:
        VUC_Metrics["Average M4_CPU_Load"] = str(vuc_average)
    if len(str(vuc_min)) != 0:
        VUC_Metrics["Minimum M4_CPU_Load"] = str(vuc_min)
def excel_report_A7(d1,d2,d3,d4,d5,dest):
    df1_a7 = pd.DataFrame({"Performance-KPIs - A7":d1.keys(),"Values":d1.values()})
    df2_a7 = pd.DataFrame({"RAM and CPU metrics - A7":d2.keys(),"Values":d2.values()})
    df1_a35 = pd.DataFrame({"Performance-KPIs - A35":d3.keys(),"Values":d3.values()})
    df2_a35 = pd.DataFrame({"RAM and CPU metrics - A35": d4.keys(), "Values": d4.values()})
    df3_vuc_cpu = pd.DataFrame({"VUC CPU LOAD": d5.keys(), "Values": d5.values()})
    writer = pd.ExcelWriter(f"{dest}\Performance.xlsx", engine="xlsxwriter")
    df1_a7.to_excel(writer,sheet_name="Performance",index=False)
    df2_a7.to_excel(writer,sheet_name="Performance",index=False,startrow=10)#linia 11 in excel
    df1_a35.to_excel(writer, sheet_name="Performance", index=False, startrow=18)#linia 19 in excel
    df2_a35.to_excel(writer, sheet_name="Performance", index=False, startrow=22)#linia 23 in excel
    df3_vuc_cpu.to_excel(writer, sheet_name="Performance", index=False,startrow=28)#linia 29 in excel
    workbook=writer.book
    header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'fg_color': '#FDE9D9', 'border': 1})
    worksheet=writer.sheets["Performance"]
    for col_num, value in enumerate(df1_a7.columns.values):
        worksheet.write(0, col_num, value, header_format)
    for col_num, value in enumerate(df2_a7.columns.values):
        worksheet.write(10, col_num, value, header_format)#match start row aboe,same for bellow
    for col_num, value in enumerate(df1_a35.columns.values):
        worksheet.write(18, col_num, value, header_format)
    for col_num, value in enumerate(df2_a35.columns.values):
        worksheet.write(22, col_num, value, header_format)
    for col_num, value in enumerate(df3_vuc_cpu.columns.values):
        worksheet.write(28, col_num, value, header_format)
    worksheet=writer.sheets["Performance"]
    formater = workbook.add_format({'border':1})
    worksheet.set_column("A:B",13,formater)
    writer.close()
def create_excel_kpi_file(path_to_excel_file,A7_dictionary,A35_dictionary,baseline):
    Excel_name = "DRT15_Baseline_kpis_values.xlsx"
    file_path = os.path.join(path_to_excel_file, Excel_name)
    if os.path.isfile(file_path):
        print("Excel file for KPIs values already existing, moving to append new row...")
        new_row = {}
        new_row.update(baseline)
        new_row.update(A7_dictionary)
        new_row.update(A35_dictionary)
        df = pd.read_excel(file_path, sheet_name="KPI")
        df = df._append(new_row, ignore_index=True)
        df.to_excel(file_path, index=False, sheet_name="KPI")
    else:
        print("Excel file for KPIs values not existing, creating Excel file and append 1st row...")
        data = {}
        data.update(baseline)
        data.update(A7_dictionary)
        data.update(A35_dictionary)
        df = pd.DataFrame([data])
        df.to_excel(file_path,index=False,sheet_name="KPI")
def create_a_list_of_actual_values():
    # Function to convert A7,A35 startup time from string to seconds float
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
    # Function to convert a string with "sec" to float because some values have simple float number or strings , like 42.5 sec
    '''Defining values to work with '''
    # bellow values are taken from current /cmdshell values
    A7_startup = [convert_to_seconds(A7_kpi_dict["A7 Startup finished time"]) if A7_kpi_dict["A7 Startup finished time"] != 'Missing value' else 0 ]  # convert signle float item to a list with 1 item
    A35_startup = [convert_to_seconds(A35_kpi_dict["A35 Startup finished time"])if A35_kpi_dict["A35 Startup finished time"] != 'Missing value' else 0]
    ecall_values, diag_values, b2b, b2c, enda, rtm = create_a7_service_kpi()
    remdiag, swlapp = create_a35_service_kpi()
    # Create a list of tuples with (list, KPI name), bassically assign a name to each list of values
    kpi_lists = [
        (ecall_values, "Max mbecall.service"),
        (diag_values, "AVG diag-mgr.service"),
        (b2b, "AVG APN2.B2B connected"),
        (b2c, "AVG APN3.B2C connected"),
        (enda, "Enda Signal Discovery Completed"),
        (rtm, "Real Time Monitoring Started"),
        (A7_startup, "A7 Startup finished time"),
        (A35_startup, "A35 Startup finished time"),
        (remdiag, "AVG Remote Diagnostics Available"),
        (swlapp, "SWL-App")]
    return kpi_lists
def measure_kpis_values_vs_static_ones(list_with_baseline_kpis,static_kpi_dict):
    def convert_to_float(value):
        if isinstance(value, str) and "sec" in value:
            return float(value.strip("sec"))
        elif isinstance(value, float):
            return value
        return value
    Sporadic_KPI_breach_percent = 5
    Systematic_KPI_breach_percent = 1
    print("Checking of following Scenario:")
    print('''3) Systematic KPI breach:
            Definition: If most or all measurements of a KPI show a regression compared to the agreed KPI value ("proposed value").
            Highest accepted value: 1% of agreed KPI value.''')
    print('''4) Sporadic KPI breach:
            Definition: If one or very few measurements of a KPI show a regression compared to the agreed KPI value ("proposed value").
            Highest accepted value: 5% of agreed KPI value.''')
    for kpi_list, kpi_name in list_with_baseline_kpis:
        if len(kpi_list) != 0:
            converted_values = [convert_to_float(value) for value in kpi_list]
            print("--------------"*2)
            print(f"Checking will be done for {kpi_name} service :")
            exceeded_systematic_kpi = 0
            exceeded_sporadic_kpi = 0
            for value in converted_values:
                if value <= static_kpi_dict[f"{kpi_name}"] * (1 + Sporadic_KPI_breach_percent/100):
                    # print(f"For value {value} seconds, Proposed KPI value is not exceeded !",static_kpi_dict[f"{kpi_name}"] * (1 + Sporadic_KPI_breach_percent/100),"seconds")
                    pass
                else:
                    print(
                        f"Value of {value} seconds from baseline of {kpi_name} is higher than {Sporadic_KPI_breach_percent}% on top of approved Static KPI of {Proposed_KPI_Avalues[kpi_name]} seconds !")
                    exceeded_sporadic_kpi += 1
                if value <= static_kpi_dict[f"{kpi_name}"] * (1 + Systematic_KPI_breach_percent / 100):
                  # print(f"For value {value} seconds, Proposed KPI value is not exceeded !")
                  pass
                else:
                    print(f"Value of {value} seconds from baseline of {kpi_name} is higher than {Systematic_KPI_breach_percent}% on top of approved KPI of  {Proposed_KPI_Avalues[kpi_name]} seconds !")
                    exceeded_systematic_kpi += 1 #increase counter
            if 1 <= exceeded_sporadic_kpi <= round(len(kpi_list)/2):
                print(f"Sporadic KPI breach for {kpi_name}")
            if exceeded_systematic_kpi >= round(len(kpi_list) * 0.8):
                print(f"Systematic KPI breach {kpi_name}")
def measure_kpis_values_vs_older_values(path_to_excel_file,baseline_values):
    def convert_to_float(value):
        if isinstance(value, str) and "sec" in value:
            return float(value.strip("sec"))
        elif isinstance(value, float):
            return value
        return value
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
                seconds = int(items[0]) + int(miliseconds)/1000
            elif "s" in part:
                seconds += int(part.replace("s", ""))
                # Convert the time to seconds
        total_seconds = minutes * 60 + seconds
        return total_seconds
    def average_kpi_value(key):
        # Extract the list of values associated with the key
        values = data_dict.get(key, [])
        # Convert string values to numeric values (integers or floats)
        numeric_values = []
        for value in values:
            try:
                numeric_value = float(value)  # Try to convert the string to a float
                numeric_values.append(numeric_value)
            except ValueError:
                pass  # Ignore values that cannot be converted to float
        # Calculate the average
        if numeric_values:
            average = sum(numeric_values) / len(numeric_values)
            # print(f"Average of '{key}': {average:.2f}")
            return average
        else:
            print(f"No numeric values found for '{key}'")
            return 0
    print("Checking of following Scenario:")
    print('''1) Systematic Regression:
        Definition: If most or all measurements of a KPI show a regression compared to actual baseline value.
        Highest accepted value: 3% of actual baseline value.''')
    print('''2) Sporadic Regression:
        Definition: If one or very few measurements of a KPI show a regression compared to actual baseline value.
        Highest accepted value: 10% of actual baseline value.''')
    # Function to convert a string with "sec" to float because some values have simple float number or strings , like 42.5 sec
    '''Defining values to work with '''
    # bellow values are taken from current /cmdshell values
    Excel_name = "DRT15_Baseline_kpis_values.xlsx"
    file_path = os.path.join(path_to_excel_file, Excel_name)
    df = pd.read_excel(file_path, sheet_name="KPI")
    data_dict = {column: df[column].tolist() for column in df.columns}
    '''Create a parse the values from the Excel Files to create a dictionary with keys and list of values for each key in order to do an average and to compare it to the actual values of the baseline'''
    for column in df.columns:       #skip 1st column as it has the baseline name
        if column == df.columns[0]:
            continue
        elif column == df.columns[1]: # for Column with 'A7 Startup finished time' to convert from string to seconds
            values = df[column].tolist()
            numeric_parts = []
            for value in values:
                if value != "Missing value":
                    numeric_parts.append(convert_to_seconds(value))
                    data_dict[column] = numeric_parts
        else:
            values = df[column].tolist()
            numeric_parts = []
            for value in values:
                value = value.strip('sec')
                value = value.replace('s','')
                numeric_parts.append(value)
                data_dict[column] = numeric_parts
    # Create a list of tuples with (list, KPI name), bassically assign a name to each list of values
    key_to_average = [column for column in df.columns]
    key_to_average.remove('Baseline_version')
    average_of_older_kpis = {}
    #for loop to have the older baseline average values
    for key in key_to_average:
        average = round(average_kpi_value(key),2)
        average_of_older_kpis[key] = average
    systematic_regression = 3
    sporadic_regression = 10
    # we must compare actual baseline values with older average values from previous baselines.
    for kpi_list, kpi_name in baseline_values :
        if len(kpi_list) != 0:
            converted_values = [convert_to_float(value) for value in kpi_list]
            print("--------------" * 2)
            print(f"Checking will be done for {kpi_name} service :")
            exceeded_systematic_regression = 0
            exceeded_sporadic_regression = 0
            for value in converted_values:
                if value <= round(average_of_older_kpis[f"{kpi_name}"] * (1 + sporadic_regression/100),2):
                    # print(f"For value {value} seconds, Proposed KPI value is not exceeded !",round(average_of_older_kpis[f"{kpi_name}"] * (1 + sporadic_regression/100),2),"seconds")
                    pass
                else:
                    print(f"Value of {value} seconds from baseline of {kpi_name} is higher than {sporadic_regression}% on top of average KPI of ",round(average_of_older_kpis[f"{kpi_name}"],2),"seconds!")
                    exceeded_sporadic_regression += 1
                if value <= round(average_of_older_kpis[f"{kpi_name}"] * (1 + systematic_regression/100),2):
                    # print(f"For value {value} seconds, Proposed KPI value is not exceeded !")
                    pass
                else:
                    print(f"Value of {value} seconds from baseline of {kpi_name} is higher than {systematic_regression}% on top of average KPI of ",round(average_of_older_kpis[f"{kpi_name}"],2),"seconds!")
                    exceeded_systematic_regression += 1
            if 1 <= exceeded_sporadic_regression <= round(len(kpi_list) / 2):
                print(f"Sporadic Regression for {kpi_name}")
            if exceeded_systematic_regression >= round(len(kpi_list) * 0.8):
                print(f"Systematic Regression for {kpi_name}")

def copy_excel_file(location_where_to_copy,path_to_excel_file):
    Excel_name = "DRT15_Baseline_kpis_values.xlsx"
    Excel_full_path = os.path.join(path_to_excel_file, Excel_name)
    if os.path.exists(Excel_full_path):
        try:
            shutil.copy(Excel_full_path,location_where_to_copy)
            print("Successfully copied")
        except OSError as e:
            print(f"Error copying due to -> {e}")
    else:
        print("Destination file not found")

if __name__ == "__main__":
    if not os.path.exists(filename):
        print(f"Location '{filename}' is invalid!")
        sys.exit(0)
    create_a7_service_kpi()
    create_a7_ram_cpu_kpi()
    create_a35_service_kpi()
    create_a35_ram_cpu_kpi()
    create_vuc_kpi(vuc_max,vuc_min,vuc_average)
    A7_kpi_dict = empty_to_value(A7_kpi_dict)
    A7_cpu_metrics = empty_to_value(A7_cpu_metrics)
    A35_kpi_dict = empty_to_value(A35_kpi_dict)
    A35_cpu_metrics = empty_to_value(A35_cpu_metrics)
    VUC_Metrics = empty_to_value(VUC_Metrics)
    excel_report_A7(A7_kpi_dict,A7_cpu_metrics,A35_kpi_dict,A35_cpu_metrics,VUC_Metrics,destination)
    # Dictionary with fixed proposed values for different KPIs
    baseline_kpis = create_a_list_of_actual_values()
    Proposed_KPI_Avalues = {"A7 Startup finished time": 120,
                            "Max mbecall.service": 42,
                            "Median mbecall.service": 42,
                            "Min mbecall.service": 42,
                            "AVG diag-mgr.service": 40,
                            "AVG APN2.B2B connected": 75,
                            "AVG APN3.B2C connected": 75,
                            "Enda Signal Discovery Completed": 120,
                            "Real Time Monitoring Started": 120,
                            "A35 Startup finished time": 120,
                            "AVG Remote Diagnostics Available": 96,
                            "SWL-App": 150}
    print("Baseline Values are :")
    for key,value in baseline_kpis:
        print(value,key,"seconds")
    print("\n")
    measure_kpis_values_vs_static_ones(baseline_kpis,Proposed_KPI_Avalues)
    measure_kpis_values_vs_older_values(sharedrive,baseline_kpis)
    copy_excel_file(destination,sharedrive)
    if baseline == "Match not found":
        print(f"Cannot load values into Excel KPI values as baseline has value : {baseline}, stopping...")
        print("Script Executed!")
        sys.exit(1)
    elif re.match("DRT15-SA515M-.*-(SECURED)$",baseline):
        print("It is not an engineering build,continuing...")
        if os.getenv("CV2X") == "YES-CV2X":
            baseline = baseline + "-CV2X"
    else:
        print(f"{baseline} looks like an engineering build, stopping...")
        print("Script Executed!")
        sys.exit(1)
    create_excel_kpi_file(sharedrive,A7_kpi_dict,A35_kpi_dict,{"Baseline_version":baseline})
    print("Script Executed!")