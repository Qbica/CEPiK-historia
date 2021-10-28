import ntpath
import os
import shutil
import time
from pathlib import Path


def directory_creator(directories):
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def archive_file(file_path, archive_path):
    filename = ntpath.basename(file_path)
    time_string = time.strftime("%d_%m_%Y_%H_%M_%S")
    final_archive_path = os.path.join(archive_path, f"{time_string}__{filename}")

    shutil.move(file_path, final_archive_path)
