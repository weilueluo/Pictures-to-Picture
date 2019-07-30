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
        self.images = None
        self.source_folder = folder
        self.files = glob(self.source_folder + '/*[jpg|png]')
        self.structure = utilities.get_database_structure(self.source_folder)
        self.database_folder = self.structure.folder
        self.color_space = None
        self.rgb_image_dict = None
        print('Database {} {}'.format(width, height))

    def process_images(self):
        print('Processing images ...', end='')
        start_time = time.time()
        if not self.images:
            raise ValueError('Please call process_and_save_files first')
        self.rgb_image_dict = dict()
        for image in self.images:
            self.rgb_image_dict[(image.avg_r, image.avg_g, image.avg_b)] = image.img
        self.images = None

        print(' [ done ] => {0:.2f}s'.format(time.time() - start_time))

    def process_and_save_files(self):
        """
        process files in self.files, according to its width and height
        :return: None
        """
        print('Processing and saving files ...')
        start_time = time.time()
        self.structure.remove_existing_files()
        self.structure.make_folders()
        self.images = []

        total = len(self.files)
        files_chunks = []
        start = 0
        while start < total - 1:
            end = start + settings.MAX_CACHE_PROCESSED_IMAGES
            files_chunks.append(self.files[start:end])
            start = end

        total_chunks = len(files_chunks)
        for chunk_index, chunk in enumerate(files_chunks):
            processed_images = []
            total_files = len(chunk)
            for file_index, file in enumerate(chunk):
                database_item = DatabaseImageItem(file)
                processed_images.append(database_item)
                self.images.append(ImageItem(database_item, self.width, self.height))
                utilities.print_progress(file_index + 1, total_files, curr_chunk=chunk_index + 1,
                                         total_chunks=total_chunks)
            utilities.save(processed_images, self.structure.get_list_name(chunk_index))
        utilities.print_done(time.time() - start_time)

    def generate_color_space(self):

        if not self.rgb_image_dict:
            raise ValueError('Please call process_images first')

        total = len(self.rgb_image_dict)
        print('Generating color space | {}'.format(total))
        start_time = time.time()
        color_space = [[[[] for _ in range(256)] for _ in range(256)] for _ in range(256)]  # 256 x 256 x 256 arrays
        for index, item in enumerate(self.rgb_image_dict.items()):
            r, g, b = item[0]
            color_space[r][g][b].append(item[1])
            utilities.print_progress(index + 1, total)
        self.images = None
        utilities.print_done(time.time() - start_time)
        start_time = time.time()
        print('cleaning color space ...', end='')
        self.color_space = utilities.remove_empty(color_space)
        print(' [ done ] => {0:.2f}s'.format(time.time() - start_time))

    def find_by_color_space(self, other, use_repeat):
        if not self.color_space:
            self.generate_color_space()
        return self.find_closest_in_color_space(other, use_repeat)

    @staticmethod
    def euclidean_dist(c1, c2):
        r1, g1, b1 = c1
        r2, g2, b2 = c2
        return (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2

    def find_by_euclidean_dist(self, other, use_repeat):
        # https: // en.wikipedia.org / wiki / Color_difference
        rgb = min(self.rgb_image_dict, key=lambda rgb: self.euclidean_dist(rgb, (other.avg_r, other.avg_g, other.avg_b)))
        item = self.rgb_image_dict[rgb]
        if not use_repeat:
            del self.rgb_image_dict[rgb]
        return item

    @staticmethod
    def euclidean_optimized_dist(c1, c2):
        r1, g1, b1 = c1
        r2, g2, b2 = c2
        r_avg = (r1 + r2) / 2
        return (2 + (r_avg / 256)) * ((r1 - r2) ** 2) + 4 * ((g1 - g2) ** 2) + (2 + ((255 - r_avg) / 256)) * (
                    (b1 - b2) ** 2)

    def find_by_euclidean_optimized_dist(self, other, use_repeat):
        # https: // en.wikipedia.org / wiki / Color_difference
        rgb = min(self.rgb_image_dict, key=lambda rgb: self.euclidean_optimized_dist(rgb, (other.avg_r, other.avg_g, other.avg_b)))
        item = self.rgb_image_dict[rgb]
        if not use_repeat:
            del self.rgb_image_dict[rgb]
        return item

    color_diff_methods = {
        'color space': 'find_by_color_space',
        'euclidean': 'find_by_euclidean_dist',
        'euclidean optimized': 'find_by_euclidean_optimized_dist',
        'cie76': 'find_by_cie76',
        'cie94': 'find_by_cie94',
        'ciede2000': 'find_by_ciede2000',
        'cmc': 'find_by_cmc'
    }

    def find_closest(self, other, use_repeat, method='euclidean_optimized'):
        if not self.rgb_image_dict:
            raise ValueError('Please call process_images first')
        other = ImageItem(other, self.width, self.height)
        return getattr(self, self.color_diff_methods[method])(other, use_repeat)

    def find_closest_in_color_space(self, other, use_repeat):
        R, G, B = other.avg_r, other.avg_g, other.avg_b

        r = int(R / 255 * (len(self.color_space) - 1) + 0.5)
        g = int(G / 255 * (len(self.color_space[r]) - 1) + 0.5)
        b = int(B / 255 * (len(self.color_space[r][g]) - 1) + 0.5)
        item = self.color_space[r][g][b][0]
        if not use_repeat:
            self.color_space[r][g][b].remove(item)
            if not self.color_space[r][g][b]:
                self.color_space[r][g].remove(self.color_space[r][g][b])
                if not self.color_space[r][g]:
                    self.color_space[r].remove(self.color_space[r][g])
                    if not self.color_space[r]:
                        self.color_space.remove(self.color_space[r])
        return item

    def remove(self, img):
        for three_d_array in self.color_space:
            for two_d_array in three_d_array:
                for array in two_d_array:
                    if img in array:
                        array.remove(img)

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

        database.images = []
        for index, chunk in enumerate(chunks):
            database.images += [ImageItem(image, database.width, database.height) for image in utilities.load(chunk)]
            utilities.print_progress(index + 1, total)
            if settings.MAX_CHUNKS_USE and settings.MAX_CHUNKS_USE == index + 1:
                print('Reached limit for max chunks use')
                break
        utilities.print_done(time.time() - start_time)

        return database

    @property
    def size(self):
        if self.rgb_image_dict:
            return len(self.rgb_image_dict)
        else:
            raise ValueError('Please process images before calling .size')
