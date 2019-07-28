import os
from itertools import repeat

import settings
import numpy as np
import time
import utilities
import math
from glob import glob
from PIL import Image
from multiprocessing import Pool


class ImageItem(object):

    def __init__(self, image, width, height):
        if isinstance(image, Image.Image):
            img = image
        elif isinstance(image, DatabaseImageItem):
            img = image.big_image
        else:
            img = Image.open(image)

        self.img = img.resize((width, height)).convert('RGB')
        self.avg_r, self.avg_g, self.avg_b = ImageItem._get_avg(self.img)

    @staticmethod
    def _get_avg(image):
        bands = np.array(image.getdata())
        sums = np.sum(bands, axis=0)
        total = len(bands)
        r_avg = sums[0] // total
        g_avg = sums[1] // total
        b_avg = sums[2] // total

        return r_avg, g_avg, b_avg

    # @staticmethod
    # def factory(inputs):
    #     return ImageItem(inputs[0], inputs[1], inputs[2])
    #
    # def crop(self, width, height):
    #     self.img = self.big_img.resize((width, height))
    #
    # @staticmethod
    # def save(image, filename):
    #     with open(filename, 'wb') as file:
    #         pickle.dump(image, file, protocol=pickle.HIGHEST_PROTOCOL)


class DatabaseImageItem(object):

    def __init__(self, filename):
        self.filename = filename
        self.big_image = Image.open(filename).resize((settings.DATABASE_IMAGE_WIDTH, settings.DATABASE_IMAGE_HEIGHT))

    @staticmethod
    def save(image, structure):
        filename = structure.get_image_filename(image.filename)
        utilities.save(image, filename)


class ImageDatabase(object):
    # DO NOT SORT TWO DATABASE AT THE SAME TIME, (that is, find closest method)
    curr_sort_object = None

    def __init__(self, width, height, folder):
        self.width = width
        self.height = height
        self.images = []
        self.source_folder = folder
        self.files = glob(self.source_folder + '/*[jpg|png]')
        self.structure = utilities.get_database_structure(self.source_folder)
        self.database_folder = self.structure.folder
        print('Database {} {}'.format(width, height))

    # def import_files(self, folder):
    #     self.files = list(set(self.files))
    #     self.folder = utilities.clean_filename(folder)
    #     print('Imported [{}] files from [{}]'.format(len(self.files), str(folder)))

    # @staticmethod
    # def _sort_by_avg_rgb_diff(img):
    #     # https://en.wikipedia.org/wiki/Color_difference
    #     # Euclidean Formula
    #     total = pow(img.avg_r - ImageDatabase.curr_sort_object.avg_r, 2) \
    #           + pow(img.avg_g - ImageDatabase.curr_sort_object.avg_g, 2) \
    #           + pow(img.avg_b - ImageDatabase.curr_sort_object.avg_b, 2)
    #     return pow(total, 0.5)

    # for multiprocessing
    # @staticmethod
    # def _process_and_save_file(inputs):
    #     database_item = DatabaseImageItem(inputs[0])  # file
    #     DatabaseImageItem.save(database_item, inputs[1])  # structure
    #     return ImageItem(database_item, inputs[2], inputs[3])  # width and height

    def process_and_save_files(self):
        """
        process files in self.files, according to its width and height
        :return: None
        """
        print('Processing and saving files ...')
        start_time = time.time()
        self.structure.make_folders()
        self.images = []
        # pool = Pool(processes=os.cpu_count())
        total = len(self.files)
        # chunksize = utilities.get_chunksize(total)
        print('\r >>> waiting for arrival of chunks ...')
        # for index, image_item in enumerate(pool.imap_unordered(ImageDatabase._process_and_save_file, zip(self.files, repeat(self.structure), repeat(self.width), repeat(self.height)), chunksize=chunksize)):
        #     self.images.append(image_item)
        #     print('\r >>> {} / {} => {}%'.format(index+1, total, math.ceil(((index+1) / total) * 100)), end='')
        # print(' done: {}s'.format(time.time() - start_time))
        files_chunks =[]
        start = 0
        while start < total-1:
            end = start + 1000
            files_chunks.append(self.files[start:end])
            start = end

        for chunk_index, chunk in enumerate(files_chunks):
            processed_images = []
            total_files = len(chunk)
            for file_index, file in enumerate(chunk):
                database_item = DatabaseImageItem(file)
                processed_images.append(database_item)
                self.images.append(ImageItem(database_item, self.width, self.height))
                print('\r >>> {} / {} => {}%'.format(file_index+1, total_files, math.ceil((file_index+1) / total_files * 100)), end='')
            utilities.save(processed_images, self.structure.get_list_name(chunk_index))
            print(' ==> saved {} / {} chunks'.format(chunk_index+1, len(files_chunks)))
        print('done {}s'.format(time.time() - start_time))

    @staticmethod
    def _get_difference(image):
        # https://en.wikipedia.org/wiki/Color_difference
        # Euclidean Formula
        other = ImageDatabase.curr_sort_object
        return ((image.avg_r - other.avg_r) ** 2 + (image.avg_g - other.avg_g) ** 2 + (
                image.avg_b - other.avg_b) ** 2) ** 0.5

    def find_closest(self, other):
        other = ImageItem(other, self.width, self.height)
        ImageDatabase.curr_sort_object = other
        return min(self.images, key=ImageDatabase._get_difference)
        # self.images.sort(key=lambda image: ImageDatabase._get_difference(image, other))
        # return self.images[0]

    def remove(self, img):
        self.images.remove(img)

    @staticmethod
    def _load(inputs):
        return ImageItem(utilities.load(inputs[0]), inputs[1], inputs[2])  # file width and height

    @staticmethod
    def load(folder, width, height):

        print('Loading database from {}'.format(folder))

        database_structure = utilities.get_database_structure(folder)

        database = ImageDatabase(width, height, folder)

        start_time = time.time()
        chunks = database_structure.get_list_names()
        total = len(chunks)

        print('Loading {} chunks from {}'.format(total, database_structure.image_folder))
        # pool = Pool(processes=os.cpu_count())
        # chunksize = utilities.get_chunksize(total)
        # print('\r >>> waiting for arrival of chunks ...')
        # for index, image_item in enumerate(pool.imap_unordered(ImageDatabase._load, zip(images, repeat(database.width), repeat(database.height)), chunksize=chunksize)):
        #     database.images.append(image_item)
        #     print('\r >>> {} / {} => {}%'.format(index + 1, total, math.ceil(((index + 1) / total) * 100)), end='')
        #
        # print(' done: {}s'.format(time.time() - start_time))
        for index, chunk in enumerate(chunks):
            chunk_list = utilities.load(chunk)
            database.images += [ImageItem(item, database.height, database.width) for item in chunk_list]
            print('\r >>> {} / {}'.format(index+1, total), end='')
        print(' done {}s'.format(time.time() - start_time))

        return database
