from datetime import datetime
import sys

ecall_button_pressed = sys.argv[1]
time_for_ecall = sys.argv[2]
kpi_time = int(sys.argv[3])

def time_calculation(t1,t2,t3):
    t1 = datetime.strptime(t1,"%H:%M:%S")
    t2 = datetime.strptime(t2, "%H:%M:%S")
    print(f"Ecall button press was at: {t1.time()}")
    print(f"MSD Sent messages was at: {t2.time()}")
    delta = t2-t1
    if delta.seconds <= t3:
        print(f"Test successfully passed, Ecall time from LPM is {delta.seconds} seconds !")
    else:
        print(f"Test not passed, Ecall time from LPM is {delta.seconds} seconds !")

time_calculation(ecall_button_pressed,time_for_ecall,kpi_time)