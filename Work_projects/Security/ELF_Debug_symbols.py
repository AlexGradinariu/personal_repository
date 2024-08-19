import pandas as pd
import argparse,os

'''
Req 420106: All software components installed on A7 and A35 systems shall not contain debug symbols.
Bassically every sw deviation is stored in "Extra files folder in the checksec_output.csv file"
Comments that are different from TBA,N/A or blank are allowed only for files which naming ends with .ko.
For the rest of the files, every comment means that some security deviation is allowed, which is strictly  forbidden.
'''

parser = argparse.ArgumentParser(description= "Parsing location")
parser.add_argument('-f', '--Path to file', help='Path to file', dest="excel_f", required=True)
args = parser.parse_args()
nad = args.excel_f + r"\nad\metrics\checksec_output.csv"
imx = args.excel_f + r"\soc\metrics\checksec_output.csv"

def check_deviations(input):
    kernelobject_issues = 0
    app_issue = 0
    dataframe = pd.read_csv(input,usecols=[10,12,13])
    df_name = list(dataframe.loc[:,"Filename"])
    df_comment = list(dataframe.loc[:,"Comment"])
    df_results = list(dataframe.loc[:,"Test Result (Passed/ Failed/ Accepted)"])

    #check kernel object with results "Failed"
    for index,x in enumerate(df_name):
        if ".ko" in x:
            if "Failed" in str(df_results[index]):
                kernelobject_issues +=1
    if kernelobject_issues != 0:
        print("--Kernel object Check--")
        print(f"{kernelobject_issues} kernel object issues found !")
        print(f"Check inside file: {input}, under column 'Test Results' what kernel object have result 'Failed' | Only allowed is `Accepted` or `Passed` ")
    else:
        print("--Kernel object Check--")
        print(f"No security deviations found inside file {input} for all files !")

    # check aplications with results "Failed"
    for index,x in enumerate(df_name):
        if "Failed" in str(df_results[index]):
            app_issue += 1
    if app_issue != 0:
        print("--Applications Check--")
        print(f"{app_issue} application problems found! ")
        print(f"Check inside file: {input}, under column 'Test Results' what application have result 'Failed' | Only allowed is `Accepted` or `Passed` ")
    else:
        print("--Applications Check--")
        print(f"No security deviations found inside file {input} for all files !")


if __name__ == "__main__":
    if os.path.exists(args.excel_f):
        print("---------------- Checking on A7 node ------------------")
        check_deviations(nad)
        print("---------------- Checking on A35 node ------------------")
        check_deviations(imx)
        print("Successfully parsed")
    else:
        print("Error ! : Please provide a valid path !")
