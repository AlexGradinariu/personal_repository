import os
import re


def check_subtitle_files(directory):
    sub_files = []
    subtitle_extensions = ('.srt', '.sub')
    if os.path.exists(directory):
        for file in os.listdir(directory):
            if file.lower().endswith(subtitle_extensions):
                file_path = os.path.join(directory, file)
                sub_files.append(file_path)
    return sub_files

def replace_broken_letter(subs_files: list):
    files_modified = []
    dictionary = {"º":"s",
                  "þ":"t",
                  "Þ":"t",
                  "ª":"s",}
    for file in subs_files:
        print('working on: ', file)
        try:
            with open(file, 'r',encoding='utf-8') as f:
                content = f.read()
                for key, value in dictionary.items():
                    if key in content:
                        content=content.replace(key, value)
                        files_modified.append(file)
            with open(file, 'w',encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error processing file {file}: {e}")
    if files_modified:
        print("file modified: ", files_modified,end="")
if __name__=="__main__":
    directory = input("Enter the directory path: ")
    files = check_subtitle_files(directory)
    replace_broken_letter(files)
    print("Done")
