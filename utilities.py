import re

def get_chunksize(files_count):
    max_divider = 100 # 100%
    files_per_divider = 0
    while files_per_divider < 1 and max_divider >= 1:
        files_per_divider = files_count // max_divider
        max_divider -= 1
    if files_per_divider < 1:
        files_per_divider = 1

    return files_per_divider


def clean_filename(filename):
    return re.sub(r'[:<>"\\/|?*]', '', str(filename))
