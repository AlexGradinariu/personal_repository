import sys
from convert_dlt import decode_dlt_buffered_reader
import matplotlib.pyplot as plt
import os,optparse
import numpy as np
import multiprocessing
import time

parser = optparse.OptionParser()
parser.add_option('-p', '--path', action="store", dest="path", help="Location to your dlt files")
parser.add_option('-d', '--destination', action= "store", dest= "destination", help= "Location to save the Plot" )
parser.add_option('-n', '--node', action= "store", dest= "node", help= "Select bentwee Nodes : IMX or NAD" )
options, args = parser.parse_args()

path = str(options.path)
destination = str(options.destination)
node = str(options.node).upper()

def parse_dlt_logs(path,node):
    filelist = [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(".dlt")]
    if len(filelist) == 0:
        print("No valid Dlt files for parsing were found for '{}' ! check script arguments and file naming ! ".format(node))
    with multiprocessing.Pool() as pool:
        results = pool.map(parse_file, filelist)
    lista_valori_cpu = [x for r in results for x in r] # iterates over multiple lists and flattens
    return  lista_valori_cpu

def parse_file(filename):
    with open(filename, "rb") as f:
        try:
            decodeddata = decode_dlt_buffered_reader(f)
        except:
            return []
        result = []
        for decodedline in decodeddata:
            if (len(decodedline['PayLoad']) > 0) and isinstance(decodedline['PayLoad'], list):
                try:
                    if 'TOPC: CPU:' in decodedline['PayLoad'][0] and node in decodedline["ECUID"]:
                        result.append(int(decodedline['PayLoad'][0].split()[2].strip("%")) + int(decodedline['PayLoad'][0].split()[4].strip("%")))
                except : pass
        return result

def plot_cpu_graph(destination,node):
    plt.plot(range(len(data)), data,"g") #green colour for chart
    plt.xlabel("Number of CPU Measurements")
    plt.ylabel("CPU usage in %")
    plt.title(f"{node} CPU Load Measurements")
    plt.grid(True)
    plt.ylim(0,100)
    try:
        plt.savefig((os.path.join(destination, f"Overall CPU Load {node}.jpg")), dpi=300)
        print("Plot successfully saved")
        plt.close()
    except Exception as e:
        print(f"Excetion occured as {e}")
    plt.close()

if __name__ == "__main__":
    if not os.path.exists(path):
        print("Location for dlt logs is invalid!")
        sys.exit(0)
    if not os.path.exists(destination):
        print("Destination is invalid!")
        sys.exit(0)
    print("Starting analysis...")
    start = time.time()
    lista_valori_cpu = parse_dlt_logs(path,node)
    print("Analyzing logs...")
    print("Creating and saving plot...")
    data = np.asarray(lista_valori_cpu)
    plot_cpu_graph(destination,node)
    end = time.time()
    total_time = end - start
    print("\n" + f"Script executed in {str(total_time)}")
    sys.exit()