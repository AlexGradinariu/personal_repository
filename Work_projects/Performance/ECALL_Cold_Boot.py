import os,sys
import numpy as np
import matplotlib.pyplot as plt
path_to_file = sys.argv[1]

def check_ecall_timer(path_to_folder):
    list_of_values = []
    for file in os.listdir(path_to_folder):
        if 'Ecall_KPI' in file:
            with open(os.path.join(path_to_folder,file),'r') as f:
                for line in f.readlines():
                    list_of_values.append(float(line.split(':')[1].strip()))
    KPI_Average = round(sum(list_of_values)/len(list_of_values),2)
    return list_of_values,KPI_Average
def plot_graph(path_to_folder):
    data = np.array(list_of_ecall_values)
    plt.ylabel('Values in Seconds')
    plt.xlabel(f"Average value in seconds is : {average_value} seconds!")
    plt.grid(True)
    plt.plot(data, 'r',label = '10 Cycles of Cold boot ECALL KPI')
    plt.title('10 Cycles of Ecall KPI from Cold Boot')
    plt.savefig(f'{path_to_folder}\Ecall KPI.jpeg')
    plt.close()

if __name__ == '__main__':
    list_of_ecall_values = check_ecall_timer(path_to_file)[0]
    average_value = check_ecall_timer(path_to_file)[1]
    plot_graph(path_to_file)
    if average_value <= 60:
      print('Average value is : {} seconds,KPI is passed !'.format(average_value))
    else:
        print('Average value is : {} seconds,KPI is not passed !'.format(average_value))
    print("Successfully parsed !")
