import zipfile
import json
import re
from datetime import datetime
import os
import shutil

def unzip_photo_archives(archive_path):
    for root, dirs, files in os.walk(archive_path):
        for file in files:
            if file.endswith(".zip"):
                zip_path = os.path.join(root, file)
                extract_to = os.path.join(root, file[:-4])
                extract_zip(zip_path, extract_to)

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

def change_date_format_if_files_with_json(path):
    pattern = re.compile(r"^\d{8}_\d{6}")
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            if dir.startswith("Photos from"):
                dir_path = os.path.join(root, dir)
                for file in os.listdir(dir_path):
                    if file.endswith(".json"):
                        json_path = os.path.join(dir_path, file)
                        base_image_name_no_ext,basename_image_w_ext,ext = resolve_base_name(file)
                        full_photo_path = os.path.join(dir_path, basename_image_w_ext)
                        if os.path.exists(full_photo_path):
                            if pattern.match(base_image_name_no_ext):
                                continue
                            with open(json_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            timestamp=int(data["photoTakenTime"]["timestamp"])
                            date_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
                            new_name = os.path.join(dir_path, date_str+ext)
                            try:
                                os.rename(full_photo_path, new_name)
                            except FileExistsError:
                                print(f"File {new_name} already exists. Skipping rename.")
                                continue
                            print(f"Renamed {base_image_name_no_ext} -> {new_name}")
                            continue

def resolve_base_name(file):
    for extension in [".jpg", ".jpeg", ".png", ".mp4"]:
        if extension in file:
            return os.path.splitext(file)[0].split(extension)[0],os.path.splitext(file)[0].split(extension)[0]+extension,extension
        else:
            return os.path.splitext(file)[0],os.path.splitext(file)[0]+extension,extension

def change_files_wiwthout_json(path):
    regex = r"Screenshot_(\d{8}_\d{6}).*"
    pattern = re.compile(regex)
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            if dir.startswith("Photos from"):
                dir_path = os.path.join(root, dir)
                for file in os.listdir(dir_path):
                    if file.endswith(".jpg"):
                        photo = os.path.join(dir_path,file)
                        match = pattern.match(file)
                        if match:
                            try:
                                new_name = os.path.join(dir_path, match.group(1) + '.jpg')
                                print(f"renamed {photo} to {new_name}")
                                os.rename(photo,new_name)
                            except Exception as e :
                                print(e)

def move_pictures_in_batxches(path):
    batch_size = 5000
    all_photos = []
    for root,dirs,files in os.walk(path):
        for directory in dirs:
            if "Photos from" in directory:
                dir_path = os.path.join(root,directory)
                for file in os.listdir(dir_path):
                    if file.lower().endswith(('.jpg','.jpeg','.png')):
                        all_photos.append(os.path.join(dir_path,file))
    all_photos.sort()
    for i in range(0, len(all_photos), batch_size):
        batch_num = i // batch_size + 1
        batch_folder = os.path.join(path, f"batch_{batch_num}")
        os.makedirs(batch_folder, exist_ok=True)

        for f in all_photos[i:i + batch_size]:
            file_name = os.path.basename(f)
            dst_path = os.path.join(batch_folder, file_name)
            print(f"moving {f} in {dst_path}")
            shutil.move(f, dst_path)
        print(f"Moved batch {batch_num} ({len(files[i:i + batch_size])} files)")

# change_date_format_if_files_with_json(r"E:\google_photos")
# rename files files
# unzip_photo_archives(r"E:\google_photos")
# change_files_wiwthout_json(r"E:\google_photos")
# move_pictures_in_batxches(r"E:\google_photos")

def move_videos(path):
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv')
    destination = os.path.join(path, "videos")
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            if dir.startswith("Photos from"):
                dir_path = os.path.join(root, dir)
                for file in os.listdir(dir_path):
                    if file.lower().endswith(video_extensions):
                        src_path = os.path.join(dir_path, file)
                        print(f"Moving video {src_path} to {destination}")
                        try:
                            shutil.move(src_path, destination)
                        except Exception as e:
                            print(f"Error moving file {src_path}: {e}")



# move_videos(r"E:\google_photos")