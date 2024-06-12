import re, optparse, os, sys
import pandas as pd
import matplotlib.pyplot as plt

'''
'This Script is use for parsing the messages and generate ram consumption per application
'Input will be the location of your messages
'''

parser = optparse.OptionParser()
parser.add_option('-p', '--path', action="store", dest="path", help="Location to your messages")
parser.add_option('-d', '--destination', action= "store", dest= "destination", help= "Location to save the Excel" )
options, args = parser.parse_args()

path = str(options.path)
destination = str(options.destination)

if not os.path.exists(path):
    parser.error('Path is invalid')
    sys.exit(0)
if len(destination) == 0:
    parser.error('Destination was not set')

RAM = []
time =[]

def took_the_file(location_of_files):
    for file in os.listdir(location_of_files):
        if file.startswith('messages'):
            with open(os.path.join(location_of_files, file), 'rb') as fr:
                        for line in fr:
                            line = str(line)
                            if 'TOPR' in line:
                                RAM.append(line.split('TOPR')[1].strip("\\n';"))
                                linetime = re.search(r'(\d+\/\d+\/\d+\s\d+:\d+:\d+).*System wide memory information', line)
                                if linetime:
                                    linetime = linetime.group(1).split(' ')[1]
                                    time.append(linetime.__str__())
    for x in RAM:
        ram_sec = x.split(';')
        for y in ram_sec:
            a = re.search(r'\(([a-zA-Z-_.\d]+)\)', y)
            b = re.search(r'\d+,\d+,(\d+)', y)
            if a and b:
                if a.group(1) not in S:
                    S.add(a.group(1))
                    D[a.group(1)] = list()
                    D[a.group(1)].append(int(b.group(1)))
                elif a.group(1) in S:
                    D[a.group(1)].append(int(b.group(1)))

def average(dict):
    for key, value in dict.items():
        if key != 'TIME':
            df_avg[key] = sum(value)/len(value)

def maximum_val(dict):
    for key, value in dict.items():
        if key != 'TIME':
            df_max[key] = max(value)

def first_value(dict):
    for key, value in dict.items():
        if key != 'TIME':
            df_first[key] = value[0]

def excel_report(all_values, avg_values, max_values, increase):
    all_values['TIME'] = time
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
              'Maximum values': df_max, 'Increase': df_increase
              }
    for sheet, frame in frames.items():
        frame.to_excel(writer, sheet_name=sheet)
    writer.close()

def memory_leak(location_of_files, first_values, maximum_values, increase):
    for file in os.listdir(location_of_files):
        if file.startswith('messages'):
            with open(os.path.join(location_of_files, file), 'rb') as fr:
                        for line in fr:
                            line = str(line)
                            if 'Memory cgroup out of memory' in line:
                                print(line.strip("\\n';b"))
    for key in first_values.keys():
        if maximum_values[key] > first_values[key]:
            if int(first_values[key]) != 0: #some values can have a 0 as result
                increase[key] = str(round(((maximum_values[key]-first_values[key])/first_values[key])*100, 2)) +"%"

def plot_figure(index):
    df = pd.read_excel(os.path.join(destination,"Ram overview.xlsx"),"Full overview")
    df1 = pd.read_excel(os.path.join(destination,"Ram overview.xlsx"),"Increase")
    lista_aplicatii = list(df1.loc[index:index+1,"App name"])
    plt.title("RAM Leaks - RAM Used over time")
    plt.grid(axis='y', alpha=0.75)
    plt.xlabel("Increments of 6 hour test")
    plt.ylabel("Amount of Ram Memory in Kb")
    plt.plot(df["TIME"].astype(str), df[lista_aplicatii].values, label=lista_aplicatii,markersize=10)
    plt.grid(axis='y', alpha=0.75)
    plt.xlabel("Increments of 6 hour test")
    plt.ylabel("Amount of Ram Memory in Kb")
    plt.legend(loc=2,prop={"size": 8})
    plt.plot()
    plt.savefig(destination+"/"f"Plot for {lista_aplicatii[0]} and {lista_aplicatii[1]} services.jpg",dpi=150)
    plt.close()

def fetch_ram_memory(location_of_files):
    for file in os.listdir(location_of_files):
        if file.startswith('messages'):
            with open(os.path.join(location_of_files, file), 'r') as file:
                for line in file:
                    line = str(line)
                    if 'TOPR System wide memory information' in line:
                        if "IMX" not in line:
                            '''Group 1 = Total memory, 
                            Group 2 = free memory, 
                            Group 3 = cached memory '''
                            try:
                                memory_regex = re.search(
                                    r"RAM:\s(\d+.\d+).MiB\s\((\d+.\d+)\sfree\s\[.*],\s(\d+.\d+)\scached,", line)
                                used_ram.append(round(float(memory_regex.group(1)) - (
                                            float(memory_regex.group(2)) + float(memory_regex.group(3))), 2))
                                available_ram.append(
                                    round(float(memory_regex.group(3)) + float(memory_regex.group(2))))
                                cached_ram.append(float(memory_regex.group(3)))
                            except Exception as e:
                                print(f"Excetion occured as {e}!")


def plot_graph_for_ram_statistics(location_of_files):
    # plotting the points
    plt.plot(used_ram, label="Used RAM", linewidth=3)
    plt.plot(available_ram, label="Available RAM", linewidth=3)
    plt.plot(cached_ram, label="Cached RAM", linewidth=3)

    # naming the x axis
    plt.ylabel('Increments in MB for Total Memory available')
    # naming the y axis
    plt.xlabel(
        f'Number of measurements during test period for ~ {round(float(len(used_ram) * 7 / 3600), 2)}' + "Hours")

    # giving a title to my graph
    plt.title('Overall A7 Node RAM Statistics')

    # show a legend on the plot
    plt.legend()
    plt.grid()

    # function to show the plot
    print("Ploting in progress...")
    plt.plot()
    try:
        plt.savefig((os.path.join(location_of_files, "Overall System RAM Statistics.jpg")), dpi=300)
        print("Plot successfully saved")
        plt.close()
    except Exception as e:
        print(f"Excetion occured as {e}")
    plt.close()

if __name__ == "__main__":
    print("Starting analysis...")
    S = set()
    D = {}
    df_avg = {}
    df_max = {}
    df_first = {}
    df_increase = {}
    took_the_file(path)
    average(D)
    maximum_val(D)
    first_value(D)
    memory_leak(path, df_first, df_max, df_increase)
    excel_report(D, df_avg, df_max, df_increase)

    '''
    'This Script is used to create PlotCharts for RAM Consumtion of shown processes
    'Input will be the location of your messages
    '''
    count = len(pd.read_excel(os.path.join(destination, "Ram overview.xlsx"), "Increase"))
    for x in range(0, count, 2):
        try:
            plot_figure(x)
        except Exception as a:
            print(f"Exception occured as: {a}")
    plt.close()
    used_ram = []
    available_ram = []
    cached_ram = []
    fetch_ram_memory(path)
    print("Value Lists where successfuly Created !")
    plot_graph_for_ram_statistics(destination)
    print(f"Successfully parsed")