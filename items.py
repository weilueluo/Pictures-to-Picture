import os
import math
import settings
import time
import utilities
import pickle
from glob import glob
from PIL import Image
from multiprocessing import Pool
from itertools import repeat


class ImageItem(object):
    """
    Variables:
        self.img
        self.big_img
        self.avg_r
        self.avg_g
        self.avg_b
        self.filename

    Class Methods:
        factory(inputs)

    Instance Methods:
        crop(self, width, height)
    """

    def __init__(self, image, width=settings.DATABASE_IMG_SIZE, height=settings.DATABASE_IMG_SIZE):
        if isinstance(image, Image.Image):
            img = image
            self.filename = None
        else:
            img = Image.open(image).convert('RGB')
            self.filename = image

        self.img = img.resize((width, height))
        self.big_img = img.resize((settings.DATABASE_IMG_SIZE, settings.DATABASE_IMG_SIZE))
        self.avg_r, self.avg_g, self.avg_b = ImageItem._get_avg(self.img)

    @staticmethod
    def _get_avg(image):
        bands = image.getdata()
        r_sum = 0
        g_sum = 0
        b_sum = 0
        for band in bands:
            r_sum += band[0]
            g_sum += band[1]
            b_sum += band[2]
        total = len(bands)
        r_avg = r_sum // total
        g_avg = g_sum // total
        b_avg = b_sum // total

        return r_avg, g_avg, b_avg

    @staticmethod
    def factory(inputs):
        return ImageItem(inputs[0], inputs[1], inputs[2])

    def crop(self, width, height):
        if width > self.big_img.width or height > self.big_img.height:
            print(' ### cropping size is larger than big_img size: {} {} < {} {}'.format(self.big_img.width,
                                                                                         self.big_img.height, width,
                                                                                         height))
        self.img = self.big_img.resize((width, height))


class ImageDatabase(object):
    """
    self.width
    self.height
    self.curr_sort_object
    self.files
    self.images
    self.images_size
    self.files_size

    self.__init__(self, width, height)
    self.add_files(self, folder)
    self.get_unprocessed_files(self)
    self.process_files(self)
    self.find_closest(self, other)
    self.remove(self, img)
    self.add_img(self, img)
    """

    # DO NOT SORT TWO DATABASE AT THE SAME TIME, (that is, find closest method)
    curr_sort_object = None

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.files = []
        self.images = []
        print('Database created with size {} {}'.format(width, height))

    def add_files(self, folder):
        print('Adding files from {} to database ... '.format(str(folder)), end='')
        self.files += glob(str(folder) + '/*[jpg|png]')
        self.files = list(set(self.files))
        print('done', self.files_size)

    @staticmethod
    def _sort_by_avg_rgb_diff(img):
        # https://en.wikipedia.org/wiki/Color_difference
        # Euclidean Formula
        sum = pow(img.avg_r - ImageDatabase.curr_sort_object.avg_r, 2) \
              + pow(img.avg_g - ImageDatabase.curr_sort_object.avg_g, 2) \
              + pow(img.avg_b - ImageDatabase.curr_sort_object.avg_b, 2)
        return pow(sum, 0.5)

    def get_unprocessed_files(self):
        processed_files = [img.filename for img in self.images]
        unprocessed_files = [file for file in self.files if file not in processed_files]
        return unprocessed_files

    def process_files(self):
        """
        process files in self.files which not in filenames of self.imgs
        :return: None
        """
        files = self.get_unprocessed_files()
        total = len(files)
        chunksize = utilities.get_chunksize(total)
        pool = Pool(processes=os.cpu_count())
        print('Processing files {} | size per % {}'.format(total, chunksize))
        # Turn all files to ImageItem Object
        print(' >>> {} / {} => {}%'.format(0, total, 0), end='')
        for index, item in enumerate(
                pool.imap_unordered(ImageItem.factory, zip(files, repeat(self.width), repeat(self.height)), chunksize)):
            print('\r >>> {} / {} => {}%'.format(index+1, total, math.ceil(((index+1) / total) * 100)), end='')
            self.images.append(item)
        print(' done')

    def find_closest(self, other):
        other = ImageItem(other, self.width, self.height)
        ImageDatabase.curr_sort_object = other
        self.images.sort(key=ImageDatabase._sort_by_avg_rgb_diff)
        ImageDatabase.curr_sort_object = None
        return self.images[0]

    def remove(self, img):
        self.images.remove(img)

    @property
    def files_size(self):
        return len(self.files)

    @property
    def images_size(self):
        return len(self.images)

    def crop(self, width, height):
        print('Re-adjusting database images ...')
        total = self.images_size
        cropped_imgs = []
        for index, img in enumerate(self.images):
            img.crop(width, height)
            cropped_imgs.append(img)
            print('\r >>> {} / {} => {}%'.format(index + 1, total,
                                                 math.ceil(((index + 1) / total) * 100)), end='')
        self.images = cropped_imgs
        self.width = width
        self.height = height
        print(' done')

    def add(self, img):
        self.images.append(img)

    @staticmethod
    def save(database, folder):
        folder = str(folder)
        image_folder = folder + '/' + settings.IMAGES_FOLDER
        database_file = folder + '/' + settings.DATABASE_FILE
        postfix = settings.POSTFIX

        if not os.path.isdir(folder):
            os.mkdir(folder)
        if not os.path.isdir(image_folder):
            os.mkdir(image_folder)

        for image in database.images:
            filename = image_folder + '/' + utilities.clean_filename(image.filename) + '.' + postfix
            with open(filename, 'wb') as file:
                pickle.dump(image, file)

        database.images = []

        with open(database_file, 'wb') as f:
            pickle.dump(database, f)

    @staticmethod
    def load_one_image(file):
        with open(file, 'rb') as f:
            return pickle.load(f)

    @staticmethod
    def load(folder):
        if not os.path.isdir(folder):
            raise pickle.PicklingError('specified database does not exists')

        folder = str(folder)
        image_folder = folder + '/' + settings.IMAGES_FOLDER
        database_file = folder + '/' + settings.DATABASE_FILE
        postfix = settings.POSTFIX
        with open(database_file, 'rb') as f:
            database = pickle.load(f)

        print('Loading existing Images ...')
        start_time = time.time()
        images = glob(image_folder + '/*' + postfix)
        total = len(images)

        pool = Pool(processes=os.cpu_count())
        chunksize = utilities.get_chunksize(total)
        for index, item in enumerate(pool.imap_unordered(ImageDatabase.load_one_image, images, chunksize=chunksize)):
            database.images.append(item)
            print('\r >>> {} / {} => {}%'.format(index + 1, total, (math.ceil((index + 1) / total * 100))), end='')

        # for index, image in enumerate(images):
        #     with open(image, 'rb') as f:
        #         database.images.append(pickle.load(f))
        #         print('\r >>> {} / {} => {}%'.format(index+1, total, (math.ceil((index+1) / total * 100))), end='')

        print(' done: {}s'.format(time.time() - start_time))

        return database

