import os
import re,itertools,sys,optparse
import zipfile

parser = optparse.OptionParser()
parser.add_option('-d', '--destination',action="store", dest="destination",help="Location where unziped files will be stored")
parser.add_option('-l', '--location',action="store",dest="location",help="Location of the .zip file")
parser.add_option('-s', '--size',action="store",dest="size",help="Total size allocated for SPI Memory BLOCK")
options, args = parser.parse_args()

destination = options.destination
location = options.location
size = int(options.size,16)

destination = destination
location = location
total_allocated = size

def unzip_file():
    with zipfile.ZipFile(location, 'r') as zip_ref:
        zip_ref.extractall(destination)
        if zip_ref:
            print("Successfully unzip_file!")
        else:
            print("Unzip_file Failed!")

def check_SAM_allocation():
    regex = "write.*\}\s(.*)\s\$"
    global TSW_SPI
    global tsw_bin_size
    TSW_SPI = []
    TSW_L_NO = None
    file = os.path.join(destination,"uuu.auto")
    tsw_bin_size = os.path.getsize(os.path.join(destination,"tsw.bin"))

    ##add values for TSW memory address##
    with open(file, "r") as lines:
        for idx, line in enumerate(lines):
            if "SPI-NOR TSW" in line:
                TSW_L_NO = idx
    with open(file, "r") as text_file:
        for line in itertools.islice(text_file, TSW_L_NO, TSW_L_NO + 4):
            l = re.search(regex, line)
            if l != None:
                TSW_SPI.append(l.group(1))
    if len(TSW_SPI) == 0:
        print("Looks like this is the new updated uuu.auto script, proceeding with searching the new line.")
        regex_update = "update.*\}\s(.*)\s\$"
        try:
            with open(file, "r") as text_file:
                for line in itertools.islice(text_file, TSW_L_NO, TSW_L_NO + 3):
                    l = re.search(regex_update, line)
                    if l != None:
                        TSW_SPI.append(l.group(1))
        except Exception as e :
            print(f"Exception occured as {e}!")

def SAM_Calculus(lista,total):
    total_allocated_spi = total
    Used_SPINOR_Memory =int(lista[0],16)
    available_for_SAM = total_allocated_spi - Used_SPINOR_Memory - tsw_bin_size
    if 4096 < available_for_SAM:
        print("SAM file size allocation within the limits")
    else:
        print("SAM file size allocation within the limits - NOK ")
    print(f"Total Memory allocated for SAM file block is {available_for_SAM} bytes,from which the tsw.bin file has {tsw_bin_size} bytes!")


unzip_file()
check_SAM_allocation()
if not os.path.exists(destination):
    print("Location is invalid!")
    sys.exit(0)
SAM_Calculus(TSW_SPI,total_allocated)
print("Successfully parsed")