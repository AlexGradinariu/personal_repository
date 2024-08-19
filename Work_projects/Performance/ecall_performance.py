from parse_dlt_logs import *
import sys,os,re

path_to_dlt = sys.argv[1]
action = sys.argv[2]
file_text_name = sys.argv[3]

def check_ecall_timer(dlt_from_swl):
    ''''Check folder for specific .dlt files'''''
    dlt_file = [os.path.join(dlt_from_swl,file) for file in os.listdir(dlt_from_swl) if file.endswith(".dlt") and "3490" in file]
    if dlt_file:
        file = dlt_file[0]
        print(f"File '{file}' found, checking for swl traces ...")
        ''''Extract SWL traces to check in offline traces if SWL is passed or not.'''''
        with open(file, "rb") as f:
            try:
                decodeddata = decode_dlt_buffered_reader(f)
            except Exception as e :
                print(f'Check exception {e}')
            for decodedline in decodeddata:
                if (len(decodedline['PayLoad']) > 0) and isinstance(decodedline['PayLoad'], list) and decodedline['APID'] == "ECAL" and "SOS_CallSw_Stat_ST3 = 1" in decodedline['PayLoad'][0]:
                    print(f"Ecall SOS BUtton was pressed at {decodedline['TMSP']} seconds TIMESTAMP")
                    sos_button = decodedline['TMSP']
                if (len(decodedline['PayLoad']) > 0) and isinstance(decodedline['PayLoad'], list) and decodedline['APID'] == "ECAL" and "SENDING_MSD" in decodedline['PayLoad'][0]:
                    print(f"Sending MSD to OECON was done at {decodedline['TMSP']} seconds TIMESTAMP")
                    sending_msd_button = decodedline['TMSP']
                    if round(abs(sending_msd_button-sos_button),2) <= 20:
                        print(f"Ecall from LPM was performed in less than 20 seconds ==>  {round(abs(sending_msd_button-sos_button),2)} seconds ")
                    else:
                        print(
                            f"Ecall from LPM was performed in more than 20 seconds ==>  {round(abs(sending_msd_button - sos_button), 2)} seconds ")

def check_overall_ecall_kpi(folder):
    list_with_values = []
    list_of_files = [os.path.join(root, file_text_name) for root, dirs, files in os.walk(folder) if file_text_name in files]
    print(f"Following files where found at location: {list_of_files}\n")
    print("=================File checking resulted that : =================")
    for file in list_of_files:
        with open(file, 'r') as f:
            for line in f:
                match = re.search('seconds\s==>\s+(.*).seconds',line)
                if match:
                    list_with_values.append((match.group(1),file))
    if len(list_with_values) < 10:
        print("Less than 10 measurements, please add extra measurements!")
        sys.exit()
    else:
        print(f"{len(list_with_values)} measurements of ecall kpi have been performed:")
        for values,location in list_with_values:
            print(f"{values} seconds measurements taken from {location}")
            # Calculate the average of ecall KPI values and Check if all values are less than 20
        if all(float(value) < 20 for value, _ in list_with_values):
            average_ecall_kpi = sum(float(value) for value, _ in list_with_values) / len(list_with_values)
            print("================= File checking resulted that: =================")
            print(f"Average of ecall KPI from LPM is less than 20 seconds : {average_ecall_kpi:.2f} seconds")
        else:
            print("Not all values are less than 20 seconds,please check the list of measurements !")

if __name__ == "__main__":
    if action == "check_kpi":
        check_ecall_timer(path_to_dlt)
    elif action == "check_results":
        check_overall_ecall_kpi(path_to_dlt+"\Traces")