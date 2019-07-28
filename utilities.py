import math
import pickle
import re
import os
from multiprocessing import current_process, Process
from threading import Thread
from glob import glob

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
        self.folder = settings.DATABASE_FOLDER.format(folder=folder)
        self.image_folder = self.folder + '/' + settings.IMAGES_FOLDER
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

def get_database_structure(folder):
    return DatabaseStructure(folder)


def save(item, filename):
    if not os.path.isfile(filename):
        with open(filename, 'wb') as file:
            pickle.dump(item, file, protocol=pickle.HIGHEST_PROTOCOL)


def load(filename):
    with open(filename, 'rb') as file:
        return pickle.load(file)

# FOR MULTIPROCESSING:
# usage: items, small list executor

def multithreading_(items, small_list_executor, info=None):
    threads = []
    num_of_items = len(items)
    num_of_threads = settings.MAX_THREAD_PER_PROCESS
    if num_of_threads == 1:
        num_of_items_per_thread = num_of_items  # if num of threads is 1
    elif num_of_threads > 1:
        num_of_items_per_thread = settings.MIN_ITEMS_PER_THREAD
        while num_of_threads > 1:
            num_of_items_per_thread = math.ceil(num_of_items / num_of_threads)
            if num_of_items_per_thread < settings.MIN_ITEMS_PER_THREAD:
                num_of_threads -= 1
                num_of_items_per_thread = num_of_items  # for condition not meet in next loop
            else:
                break
    else:
        raise ValueError('number of threads must be at least 1, please check settings.py')

    if num_of_threads > num_of_items:
        num_of_threads = num_of_items

    for thread_count in range(0, num_of_threads):
        start = thread_count * num_of_items_per_thread
        end = (thread_count + 1) * num_of_items_per_thread
        items_for_this_thread = items[start:end]
        threads.append(Thread(target=small_list_executor, args=(items_for_this_thread, info), daemon=True))
    print('  |->', current_process().name, '=>', len(threads), 'threads =>', num_of_items, 'items')
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


# breaks the given items into small lists in different process and threads,
# pass these small lists to small_list_executor
# results_saver is used to save results if any
# raise ValueError if num of max threads specified in settings is < 1
def multiprocessing_(items, small_list_executor, info=None):
    print('Starting multiprocessing...')
    processes = []
    num_of_items = len(items)
    num_of_processes = os.cpu_count()
    num_of_items_per_process = settings.MIN_ITEMS_PER_THREAD
    while num_of_processes > 1:
        num_of_items_per_process = math.ceil(num_of_items / num_of_processes)
        if num_of_items_per_process < settings.MIN_ITEMS_PER_THREAD:
            num_of_processes -= 1
            num_of_items_per_process = num_of_items  # if next condition failed, num_of_processes = 1
        else:
            break

    if num_of_processes > num_of_items:
        num_of_processes = num_of_items

    for process_count in range(0, num_of_processes):
        start = process_count * num_of_items_per_process
        end = (process_count + 1) * num_of_items_per_process
        items_for_this_process = items[start:end]
        processes.append(
            Process(target=multithreading_, args=(items_for_this_process, small_list_executor, info),
                    daemon=True))
    print('|--', current_process().name, '=>', len(processes), 'processes =>', num_of_items, 'items')
    for process in processes:
        process.start()
    for process in processes:
        process.join()
