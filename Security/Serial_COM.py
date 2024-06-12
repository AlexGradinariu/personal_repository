import serial
import time,argparse

parser = argparse.ArgumentParser(description= "Parsing some numbers")
parser.add_argument('-c', '--command', help='Command to be send', dest="your_command", required=False)
parser.add_argument('-p', '--port', help='Modem port', dest="port", required=True)
parser.add_argument('-a', '--action', help='Type of command,send or listen', dest="type", required=True)
parser.add_argument('-d', '--duration', help='How long to listen', dest="duration", required=False)
args = parser.parse_args()
your_command = args.your_command
port = str(args.port)
action = str(args.type)
duration = args.duration

'''How to use it ,example:
Send commands on a COM port : -a write -p COM7 -c your_command 
Listen on a COM port : 
-a listen -p COM7 -d 160(time in seconds)
'''

def getSerialOrNone(port):
    try:
        ser = serial.Serial(port= port)
        ser.close()
        return True
    except serial.SerialException as e:
        print(e)
        return False

def listen_port(port,time_value):
    if getSerialOrNone(port):
        print(f"Start listening on port {port}...")
        serial_output = serial.Serial(port=port, baudrate=115200,timeout=0,rtscts=0,xonxoff=0)
        timeout = time.time() + int(time_value)
        while True and time.time() < timeout:
            BarCode = serial_output.readline()
            if len(BarCode) >= 3:
                s = BarCode.decode("ISO-8859-1").strip("\r\n")
                print(s)
        serial_output.close()
    else:
        print("Port is not usable")

def write_commands_on_port(port,cmd):
    if getSerialOrNone(port):
        print(f"Start listening on port {port}...")
        timeout_duration = 2  # Timeout duration in seconds
        serial_output = serial.Serial(port=port, baudrate=115200,timeout=0,rtscts=1,xonxoff=1)
        serial_output.write(f"{cmd}\r".encode())
        start_time = time.time()  # Start the timer
        while (time.time() - start_time) < timeout_duration:
            barcode = serial_output.readline()
            if barcode:
                s = barcode.decode("utf-8").strip("\r\n")
                print(s)
            # break  # Break the outer loop after receiving the entire output
    else:
        print("port not usable")



if __name__ == "__main__":
    if action == "listen":
        listen_port(port,int(duration))
    elif action == 'write':
        write_commands_on_port(port,your_command)
    else:
        print("Your command is not correct !")