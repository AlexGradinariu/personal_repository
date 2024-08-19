import os,sys
import numpy as np
import matplotlib.pyplot as plt
path_to_file = sys.argv[1]
node = sys.argv[2]

def get_disk_values(path_to_folder):
    imx_values = []
    nad_values = []
    for file in os.listdir(path_to_folder):
        if 'df_values' in file:
            with open(os.path.join(path_to_folder,file),'r') as f:
                for line in f.readlines():
                    if "nad value" in line:
                        nad_values.append(float(line.split(':')[1].strip()))
                    elif "imx value"in line:
                        imx_values.append(float(line.split(':')[1].strip()))
    return imx_values,nad_values
def plot_graph(path_to_folder,node):
    data = np.array(listf_of_disk_values)
    plt.ylabel('Values in %')
    plt.grid(True)
    plt.plot(data, 'r',label=f'{node} Node')
    plt.title('Percentage of /data disk occupation - {} node'.format(node))
    plt.savefig(f'{path_to_folder}\Disk_occupation - {node} node.jpeg')
    plt.close()

if __name__ == '__main__':
    if node == "IMX":
        listf_of_disk_values = get_disk_values(path_to_file)[0]
        plot_graph(path_to_file,node)
        print(f"Graph created for {node}")
    elif node == "NAD":
        listf_of_disk_values = get_disk_values(path_to_file)[1]
        plot_graph(path_to_file, node)
        print(f"Graph created for {node}")
    print("Successfully parsed !")
