import serial, time, re, argparse, os, sys

parser = argparse.ArgumentParser(description= "Parsing for cyclic resets")
parser.add_argument('-e', '--end', help='Ending log', dest="end", required=True)
parser.add_argument('-s', '--start', help='Starting log', dest="start", required=True)
parser.add_argument('-l', '--port', help='Location of logs', dest="path", required=True)
parser.add_argument('-t0', '--start_log', help='t0', dest="t0", required=True)
parser.add_argument('-t1', '--end_log', help='t1', dest="t1", required=True)
args = parser.parse_args()
end = args.end
path = args.path
start = args.start
t0 = args.t0
t1 = args.t1


def parsing_logs(path, l):
    filenameList = list()
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.startswith("messages"):
                filenameList.append(os.path.join(root, file))
    if filenameList:
        filenameList.sort(reverse= True)
    else:
        print("Can not find messages at", path)
    print(filenameList)
    flag = 0
    for file in filenameList:
        with open(file, 'rb') as file_r:
            for line in file_r:
                line = str(line).strip("b'\\n\"")
                if start in line :
                    l.clear()
                    flag = 1
                elif line.endswith(end) and flag == 1:
                    flag = 0
                    l.append(line)
                if flag == 1:
                    l.append(line)
    with open(os.path.join(path, 'wantedPart.txt'), 'w') as file_w:
        file_w.write("\n".join(l))

def diff_time(t0, t1, l):
    flag = 0
    for line in l:
        if t0 in line:
            print(line)
            t0_p = detect_special_characer_and_replace(t0)
            t0_p = re.search(r'\[\s*(\d+.\d+)\].*{}'.format(t0_p),line)
            t0_p = float(t0_p.group(1))
            print("T0 :", str(t0_p))
            flag = 1
        if t1 in line and flag:
            print(line)
            t1_p = detect_special_characer_and_replace(t1)
            t1_p = re.search(r'\[\s*(\d+.\d+)\].*{}'.format(t1_p), line)
            t1_p = float(t1_p.group(1))
            print("T1 :", str(t1_p))
            flag = 0
    try:
        print(f"KPI = {t1_p - t0_p}")
    except Exception as e:
        print(e)

def detect_special_characer_and_replace(pass_string):
  regex= re.compile('[@_!#$%^&*()<>?/\|}{~:]')
  if(regex.search(pass_string) == None):
    res = False
  else:
    res = True
  if res:
      for x in pass_string:
          if re.search(r'[()<>{}?:~#$\[\]]', x):
              pass_string = pass_string.replace(x, "\{}".format(x))
  return pass_string


if __name__ == "__main__":
    l = []
    parsing_logs(path, l)
    diff_time(t0, t1, l)

