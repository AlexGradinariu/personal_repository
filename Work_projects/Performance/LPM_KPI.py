import os
import re,sys
import pandas as pd

m_test_dir = sys.argv[1]
destination = sys.argv[2]
def get_DNO_kpi(M_test_suite):
    regex_suspended  = '\[(.*)\]\sresume cycles:'
    system_suspended = ''
    file_to_search = ''
    for root,dirs,files in os.walk(M_test_suite):
        for file in files:
            if file.startswith('dmesg_dno'):
                file_to_search = os.path.join(root,file)
    #get suspended time
    with open(file_to_search) as f:
        for line in f.readlines():
            match_suspend = re.search(regex_suspended,line)
            if match_suspend :
                system_suspended = float(match_suspend.group(1))
    #get APNs resumed times
    print("---DNO-----------------------------")
    B2B = "missing trace"
    B2C = "missing trace"
    SWL = "missing trace"
    ECALL = "missing trace"
    A35 = "missing trace"
    with open(file_to_search) as f:
        for line in f.readlines():
            try:
                if "B2B Ready :" in line:
                    B2B = float(line.strip().split(':')[1])
                    print(f"B2B started time is {round((B2B - system_suspended), 2)} seconds")
                    B2B = f"{round((B2B - system_suspended), 2)} seconds"
                if "B2C Ready :" in line:
                    B2C = float(line.strip().split(':')[1])
                    print(f"B2C started time is {round((B2C - system_suspended), 2)} seconds")
                    B2C = f"{round((B2C - system_suspended), 2)} seconds"
                if "SWL Ready :" in line:
                    SWL = f"{round(float(line.strip().split(':')[1]),2)} seconds"
                    print(f"SWL started time is {SWL}")
                if 'ECALL Ready :' in line:
                    ECALL = float(line.strip().split(':')[1])
                    print(f"ECALL started time is {round((ECALL - system_suspended), 2)} seconds")
                    ECALL = f"{round((ECALL - system_suspended), 2)} seconds"
                if 'A35 Ready :' in line:
                    A35 = float(line.strip().split(':')[1])
                    print(f'A35 reaching multi-user in {round(A35, 2)} seconds')
                    A35 = (f"{round(A35, 2)} seconds")
            except Exception as e :
                print(f"Exception occured as : {e}")
    return B2B, B2C,SWL, ECALL, A35

def get_CDNO_kpi(M_test_suite):
    regex_suspended = '\[(.*)\]\sresume cycles:'
    system_suspended = ''
    file_to_search = ''
    for root, dirs, files in os.walk(M_test_suite):
        for file in files:
            if file.startswith('dmesg_cdno'):
                file_to_search = os.path.join(root, file)
    # get suspended time
    with open(file_to_search) as f:
        for line in f.readlines():
            match_suspend = re.search(regex_suspended, line)
            if match_suspend:
                system_suspended = float(match_suspend.group(1))
    print("---CDNO-----------------------------")
    B2C = "missing trace"
    SWL = "missing trace"
    ECALL = "missing trace"
    A35 = "missing trace"
    # get APNs resumed times
    with open(file_to_search) as f:
        for line in f.readlines():
            try:
                if "B2C Ready :" in line:
                    B2C = float(line.strip().split(':')[1])
                    print(f"B2C started time is {round((B2C - system_suspended), 2)} seconds")
                    B2C = f"{round((B2C - system_suspended), 2)} seconds"
                if "SWL Ready :" in line:
                    SWL = f"{round(float(line.strip().split(':')[1]), 2)} seconds"
                    print(f"SWL started time is {SWL}")
                if 'ECALL Ready :' in line:
                    ECALL = float(line.strip().split(':')[1])
                    print(f"ECALL started time is {round((ECALL - system_suspended), 2)} seconds")
                    ECALL = f"{round((ECALL - system_suspended), 2)} seconds"
                if 'A35 Ready :' in line:
                    A35 = float(line.strip().split(':')[1])
                    print(f'A35 reaching multi-user in {round(A35, 2)} seconds')
                    A35 = (f"{round(A35, 2)} seconds")
            except Exception as e :
                print(f"Exception occured as : {e}")
    return B2C, SWL, ECALL, A35

def highlight_unknown(s):
    return ['color: red' if 'missing trace' in str(v).lower() else '' for v in s]
def style_dataframe(df):
    return df.style.apply(highlight_unknown, axis=1)

def create_excel_table(DNO,CDNO):#function takes two dictionaries
    DF = pd.DataFrame({"Performance-KPIs in LPM": DNO.keys(), "DNO": DNO.values(),"CDNO": CDNO.values()})
    styled_df = style_dataframe(DF)
    styled_df.to_excel(f"{destination}\Low_PM_KPIs.xlsx", index=False)


if __name__ == "__main__":
    #DNO Dictionary to be filled in with bellow values
    DNO = {}
    B2B_DNO,B2C_DNO, SWL_DNO, ECALL_DNO, A35_DNO = get_DNO_kpi(m_test_dir)
    DNO["A35 - Normal State Reached"] = A35_DNO
    DNO["B2B APN - IP allocated"] = B2B_DNO
    DNO["B2C APN - IP allocated"] = B2C_DNO
    DNO["SWL service ready"] = SWL_DNO
    DNO["eCall service ready"] = ECALL_DNO
    B2C_CDNO, SWL_CDNO, ECALL_CDNO, A35_CDNO = get_CDNO_kpi(m_test_dir)
    #CDNO Dictionary to be filled in with bellow values
    CDNO = {}
    CDNO["A35 - Normal State Reached"] = A35_CDNO
    CDNO["B2B APN - IP allocated"] = 'N/A' # IN CDNO, B2B is always connected
    CDNO["B2C APN - IP allocated"] = B2C_CDNO
    CDNO["SWL service ready"] = SWL_CDNO
    CDNO["eCall service ready"] = ECALL_CDNO
    create_excel_table(DNO,CDNO)
    print("Script completed")