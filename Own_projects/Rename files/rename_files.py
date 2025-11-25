import os

def rename_files(folder_path, old_prefix, new_prefix):

    for filename in os.listdir(folder_path):
        if filename.startswith(old_prefix):
            # Construct the new file name
            new_name = filename.replace(old_prefix, new_prefix, 1)

            # Build full paths
            old_file = os.path.join(folder_path, filename)
            new_file = os.path.join(folder_path, new_name)

            # Rename the file
            os.rename(old_file, new_file)
            print(f"Renamed: {filename} → {new_name}")

rename_files(r"C:\Users\uic81314\Desktop\test\proj.vuc.davinci.all\Config\ECUC","r20_tc4","vra20")