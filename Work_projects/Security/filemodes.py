import pandas as pd
import argparse

parser = argparse.ArgumentParser(description= "Parsing location")
parser.add_argument('-f', '--Path to file', help='Path to file', dest="excel_f", required=True)

args = parser.parse_args()
excel_f=args.excel_f

def extracting_errors():

    excel_file = excel_f
    dataframe1 = pd.read_csv(excel_file,usecols=[1,2,3])
    df2 = list(dataframe1.loc[:,"unrestricted files"])
    df3 = list(dataframe1.loc[:,"Team"])
    flag = False

    for index,x in enumerate(df2):
        if x > 0:
            print(f"The following team: {df3[index]} has {df2[index]} files unchecked")
        else:
            flag = True
    if (flag):
        print("No error found")

if __name__ == "__main__":
    extracting_errors()