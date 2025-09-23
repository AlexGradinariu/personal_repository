import os
import re


def check_subtitle_files(directory):
    sub_files = []
    subtitle_extensions = ('.srt', '.sub')
    if os.path.exists(directory):
        for files in os.listdir(directory):
            if files.lower().endswith(subtitle_extensions):
                file_path = os.path.join(directory, files)
                sub_files.append(file_path)
    return sub_files

def replace_broken_letter(subs_files: list):
    dictionary = {"º":"s",
                  "þ":"t",
                  "Þ":"t",
                  "ª":"s",}
    for file in subs_files:
        try:
            with open(file, 'r') as f:
                content = f.read()
                for key, value in dictionary.items():
                    if key in content:
                        content=content.replace(key, value)
            with open(file, 'w') as f:
                f.write(content)
                print(f"Modified file{file}")
        except Exception as e:
            print(f"Error processing file {file}: {e}")
if __name__=="__main__":
    directory = input("Enter the directory path: ")
    files = check_subtitle_files(directory)
    replace_broken_letter(files)