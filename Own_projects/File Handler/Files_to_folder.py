import os
import shutil
def move_files_into_dirs(path):
    file_name = []
    for root,dirs,files in os.walk(path):
        for file in files:
            print(f"File {file} found !")
            file_name.append(file.split('.')[0])
    for file in file_name:
        print(f"creating dir {file}")
        os.mkdir(os.path.join(root,file))
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            folder = os.path.join(path, item)
            for file in os.listdir(path):
                if os.path.isfile(os.path.join(path, file)):
                    file = os.path.join(path, file)
                    if file.startswith(folder):
                        print(f"moving {file} to {folder}")
                        shutil.move(file,folder)

move_files_into_dirs(r'C:\Users\uic81314\Desktop\docker_git_tools')