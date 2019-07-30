import math
import pickle
import re
import os
import time
from multiprocessing import current_process, Process
from threading import Thread
from glob import glob
import shutil

import settings


def get_chunksize(files_count):
    max_divider = 100  # 100%
    files_per_divider = 0
    while files_per_divider < 1 and max_divider >= 1:
        files_per_divider = files_count // max_divider
        max_divider -= 1
    if files_per_divider < 1:
        files_per_divider = 1

    return files_per_divider


def clean_filename(filename):
    return re.sub(r'[:<>"\\/|?*]', '', str(filename))


class DatabaseStructure(object):
    """
    Variables:
        self.folder
        self.image_folder
        self.database_file
        self.postfix
    """

    def __init__(self, folder):
        self.folder = clean_filename(settings.DATABASE_FOLDER.format(folder=folder))
        self.image_folder = self.folder + '/' + clean_filename(settings.IMAGES_FOLDER)
        self.postfix = settings.POSTFIX

    def get_image_filename(self, image_name):
        return (self.image_folder + '/{}.' + self.postfix).format(clean_filename(image_name))

    def make_folders(self):
        if not os.path.isdir(self.folder):
            os.mkdir(self.folder)
        if not os.path.isdir(self.image_folder):
            os.mkdir(self.image_folder)

    def get_list_name(self, number):
        return (self.image_folder + '/{}.' + self.postfix).format(number)

    def get_list_names(self):
        return glob(self.image_folder + '/*' + self.postfix)

    def remove_existing_files(self):
        if os.path.isdir(self.folder):
            shutil.rmtree(self.folder)


def get_database_structure(folder):
    return DatabaseStructure(folder)


def save(item, filename):
    if not os.path.isfile(filename):
        with open(filename, 'wb') as file:
            pickle.dump(item, file, protocol=pickle.HIGHEST_PROTOCOL)


def load(filename):
    with open(filename, 'rb') as file:
        return pickle.load(file)


is_first_print = True
last_percent = None
last_percent_time_left = None
last_percent_print_time = None
est_time_lefts = [0, 0, 0]


# est time left is very unaccurate
def print_progress(curr, total, curr_chunk=None, total_chunks=None):
    global is_first_print
    global last_percent
    global last_percent_time_left
    global last_percent_print_time
    global est_time_lefts
    curr_percent = math.floor(curr / total * 100)
    curr_time = time.time()
    if is_first_print:
        est_time_left = float("inf")
        is_first_print = False
        last_percent_time_left = est_time_left
        last_percent_print_time = curr_time
    elif last_percent == curr_percent:
        est_time_left = last_percent_time_left
    else:
        bad_est_time_left = (curr_time - last_percent_print_time) / (curr_percent - last_percent) * (100 - curr_percent)
        est_time_lefts.append(bad_est_time_left)
        est_time_lefts = est_time_lefts[1:]
        est_time_left = sum(est_time_lefts) / len(est_time_lefts)
        last_percent_time_left = est_time_left
        last_percent_print_time = curr_time

    last_percent = curr_percent

    print('\r >>> {0} / {1} => {2}% | Time Left est. {3:.2f}s'.format(curr, total, curr_percent, est_time_left), end='')

    if curr_chunk and total_chunks:
        print(' | {} / {}'.format(curr_chunk, total_chunks), end='')


def print_done(msg):
    if isinstance(msg, str):
        print(' [ done ] => {msg}s'.format(msg=msg))
    else:  # a float, time taken
        print(' [ done ] => {0:.2f}s'.format(msg))
    global is_first_print
    global last_percent
    global last_percent_time_left
    global last_percent_print_time
    global est_time_lefts
    is_first_print = True
    last_percent = None
    last_percent_print_time = None
    last_percent_time_left = None
    est_time_lefts = [0, 0, 0]


# def remove_empty(a_list):
#     if not isinstance(a_list, list):
#         return a_list
#
#     if not a_list:
#         return False
#
#     result = []
#     for item in a_list:
#         item = remove_empty(item)
#         if item:
#             result.append(item)
#     return result


def remove_empty(a_list):
    if not isinstance(a_list, list):
        return a_list
    result = []
    for item in a_list:
        if item:
            item = remove_empty(item)
            if item:
                result.append(item)
    return result
