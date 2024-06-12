import re
from convert_dlt import decode_dlt_buffered_reader
import matplotlib.pyplot as plt
import os,optparse
import multiprocessing
import time
import sys

parser = optparse.OptionParser()
parser.add_option('-p', '--path', action="store", dest="path", help="Location to your dlt files")
parser.add_option('-d', '--destination', action= "store", dest= "destination", help= "Location to save the Plot" )
parser.add_option('-n', '--node', action= "store", dest= "node", help= "Select bentwee Nodes : IMX or NAD" )
options, args = parser.parse_args()

path = str(options.path)
destination = str(options.destination)
node = str(options.node).upper()

regex = "RAM:\s(\d+.\d+).MiB\s\((\d+.\d+)\sfree\s\[.*],\s(\d+.\d+)\scached,"

'''The get_RAM_values_chunk() function processes each file in the chunk, and returns the results as a tuple of three lists:
 results_used_ram, result_avlb_ram, and results_cached_ram. 
 The get_values_from_traces() function then concatenates the results from all chunks and returns them as three separate lists.'''

def get_values_from_traces(path,node):
    filelist = [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(".dlt")]
    if len(filelist) == 0:
        print("No valid Dlt files for parsing were found ! check script arguments and file naming ! ")
    # split the filelist into chunks of multiple files , good when you have lots of dlt files
    chunksize = 10
    file_chunks = [filelist[i:i + chunksize] for i in range(0, len(filelist), chunksize)]
    # process each chunk in parallel
    with multiprocessing.Pool() as pool:
        results = pool.map(get_RAM_values, [(chunk, node) for chunk in file_chunks])
    # concatenate the results from all chunks
    used_RAM = [x for r in results for x in r[0]]
    available_RAM = [x for r in results for x in r[1]]
    cached_RAM = [x for r in results for x in r[2]]
    return used_RAM, available_RAM, cached_RAM
def get_RAM_values(args):
    filelist, node = args
    results_used_ram = []
    result_avlb_ram = []
    results_cached_ram = []
    for filename in filelist:
        with open(filename, "rb") as f:
            try:
                decodeddata = decode_dlt_buffered_reader(f)
            except:
                continue
            for decodedline in decodeddata:
                if (len(decodedline['PayLoad']) > 0) and isinstance(decodedline['PayLoad'], list):
                    try:
                        if 'TOPR System wide memory information' in decodedline['PayLoad'][0] and node in decodedline["ECUID"] :
                            output = re.search(regex,decodedline['PayLoad'][0])
                            results_used_ram.append(round(float(output.group(1)) - (float(output.group(2)) + float(output.group(3))), 2))
                            result_avlb_ram.append(round(float(output.group(3)) + float(output.group(2))))
                            results_cached_ram.append(float(output.group(3)))
                    except : pass
    return results_used_ram,result_avlb_ram,results_cached_ram

def plot_graph_for_ram_statistics(location_of_files,node):
    # plotting the points
    plt.plot(used_ram, label="Used RAM", linewidth=3)
    plt.plot(available_ram, label="Available RAM", linewidth=3)
    plt.plot(cached_ram, label="Cached RAM", linewidth=3)

    # naming the x axis
    plt.ylabel('Increments in MB for Total Memory available')
    # naming the y axis
    plt.xlabel(f'Number of measurements during test period for ~ {round(float(len(used_ram) * 7 / 3600), 2)}' + "Hours")

    # giving a title to my graph
    plt.title(f'Overall {node} Node RAM Statistics')

    # show a legend on the plot
    plt.legend()
    plt.grid()

    # function to show the plot
    print("Ploting in progress...")
    plt.plot()
    try:
        plt.savefig((os.path.join(location_of_files, f"Overall {node} System RAM Statistics.jpg")), dpi=300)
        print("Plot successfully saved")
        plt.close()
    except Exception as e:
        print(f"Exception occured as {e}")
    plt.close()

if __name__ == "__main__":
    if not os.path.exists(path):
        print("Location for dlt logs is invalid!")
        sys.exit(0)
    if not os.path.exists(destination):
        print("Destination is invalid!")
        sys.exit(0)
    start = time.time()
    print("Starting analysis...")
    used_ram , available_ram , cached_ram = get_values_from_traces(path,node)
    plot_graph_for_ram_statistics(destination,node)
    end = time.time()
    total_time = end - start
    print("\n" + f"Script executed in {str(total_time)}")
    sys.exit()
