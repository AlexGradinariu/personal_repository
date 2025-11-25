import os
import re


def check_subtitle_files(directory):
    sub_files = []
    subtitle_extensions = ('.srt', '.sub')
    if os.path.exists(directory):
        for root,dirs,files in os.walk(directory):
            for directory in dirs:
                base_dir = os.path.join(root,directory)
                for file in os.listdir(base_dir):
                    if file.lower().endswith(subtitle_extensions):
                        file_path = os.path.join(base_dir, file)
                        sub_files.append(file_path)
    return sub_files

def replace_broken_letter(subs_files: list):
    dictionary = {"º":"s",
                  "þ":"t",
                  "Þ":"t",
                  "ª":"s",}
    for file in subs_files:
        flag = False
        try:
            with open(file, 'r',encoding='utf-8') as f:
                content = f.read()
                for key, value in dictionary.items():
                    if key in content:
                        print('Found broken letter:', key, 'in file:', file)
                        flag = True
                        content=content.replace(key, value)
            if flag:
                with open(file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    print(f"Modified file{file}")
            else:
                print(f"No broken letters found in file {file}")
        except Exception as e:
            print(f"Error processing file {file}: {e}")
if __name__=="__main__":
    directory = input("Enter the directory path: ")
    files = check_subtitle_files(directory)
    replace_broken_letter(files)