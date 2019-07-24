
import os
import sys
import time
import math
import pickle
import argparse
from glob import glob
from PIL import Image
from itertools import repeat
from multiprocessing import Pool

sys.stdout.reconfigure(encoding='utf-8')

DATABASE_IMG_SIZE = 100

class Image_:

    def __init__(self, image, width, height):
        if isinstance(image, Image.Image):
            img = image
        else:
            img = Image.open(image).convert('RGB')

        self.img = img.resize((width, height))
        self.big_img = img.resize((DATABASE_IMG_SIZE,DATABASE_IMG_SIZE)) # FOR SAVING
        self.avg_r, self.avg_g, self.avg_b = Image_._get_avg(self.img)

    def _get_avg(img):
        bands = img.getdata()
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

        return (r_avg, g_avg, b_avg)

    def factory(inputs):
        return Image_(inputs[0], inputs[1], inputs[2])

    def crop(self, width, height):
        self.img = self.big_img.resize((width, height))

class ImageDatabase:
    def __init__(self, folder, size, details=None):
        print('Creating database from folder:', folder)
        self.width = size[0]
        self.height = size[1]
        print('database images size: width', self.width, 'height', self.height)
        self.curr_sort_object = None
        # width and height for each images in this database
        self.files = glob(folder + '/*[jpg|png]')
        self.imgs = []
        print('Pictures found:', self.files_size)

    def _sort_by_avg_rgb_diff(img):
        # https://en.wikipedia.org/wiki/Color_difference
        # Euclidean Formula
        sum = pow(img.avg_r - ImageDatabase.curr_sort_object.avg_r, 2) \
            + pow(img.avg_g - ImageDatabase.curr_sort_object.avg_g, 2) \
            + pow(img.avg_b - ImageDatabase.curr_sort_object.avg_b, 2)
        return pow(sum, 0.5)

    def get_chunksize(files_count):
        max_divider = 100 # 100%
        files_per_divider = 0
        while files_per_divider < 1 and max_divider >= 1:
            files_per_divider = files_count // max_divider
            max_divider -= 1
        return files_per_divider

    def generate_images(self):
        print('Processing Pictures found ...')
        cpus = os.cpu_count()
        total_files = self.files_size
        chunksize = ImageDatabase.get_chunksize(total_files)
        if chunksize < cpus:
            chunksize = 1
        pool = Pool(processes=cpus)
        for index, item in enumerate(pool.imap_unordered(Image_.factory, zip(self.files, repeat(self.width), repeat(self.height)), chunksize)):
            print('\r >>> {} / {} => {}%'.format(index, total_files, math.ceil((index / total_files) * 100)), end='')
            self.imgs.append(item)
        print(' done')

    def find_closest(self, other):
        other = Image_(other, self.width, self.height)
        ImageDatabase.curr_sort_object = other
        self.imgs.sort(key=ImageDatabase._sort_by_avg_rgb_diff)
        return self.imgs[0]

    def remove(self, img):
        self.imgs.remove(img)

    @property
    def files_size(self):
        return len(self.files)

    def crop(self, width, height):
        print('re-adjusting database images ...')
        total_imgs = len(self.imgs)
        chunksize = ImageDatabase.get_chunksize(total_imgs)
        pool = Pool(processes=os.cpu_count())
        cropped_imgs = []
        for index, img in enumerate(list(self.imgs)):
            img.crop(width, height)
            cropped_imgs.append(img)
            self.imgs.remove(img)
            print('\r >>> {} / {} => {}%'.format(index+1, total_imgs, math.ceil(((index+1) / total_imgs) * 100)), end='')
        self.imgs = cropped_imgs
        print(' done')



def _load_database(folder, chunk_width, chunk_height, repeat):
    file_name = folder + '.imagedatabase'
    database = ImageDatabase(folder, (chunk_width, chunk_height))
    files_found = database.files_size
    total_chunks = chunk_width * chunk_height

    if os.path.exists(file_name):
        print('found existing database:', file_name)
        if chunk_width > DATABASE_IMG_SIZE or chunk_height > DATABASE_IMG_SIZE:
            raise pickle.PicklingError('Database size does not satisfy requirement for this image, rebuilding ...')
        try:
            with open(file_name, 'rb') as file:
                existing_database = pickle.loads(file.read())

            files_in_old_database = existing_database.files_size

            if files_found == files_in_old_database:
                print('using existing database')
                existing_database.crop(chunk_width, chunk_height)
                return existing_database

            while True:
                ans = input('existing database has different number of images as in specified folder, old:{}, folder:{}, use existing? [y/n]:'.format(files_in_old_database, files_found))
                if ans == 'y':
                    return existing_database
                elif ans == 'n':
                    break
                print('Please give answer as \'y\' or \'n\'')

        except pickle.PicklingError as e:
            print('failed to load database:', file_name, 'due to:', str(e))
            print('creating new database from given folder')


    if not repeat and total_chunks > files_found:
        raise ValueError('size of database is not enough:', total_chunks, '>', files_found)

    if not repeat and total_chunks > files_found / 4:
        print('database is not optimal for', total_chunks, 'pieces from', files_found, 'try set to > 1:4 if possible')

    start_time = time.time()
    database.generate_images()
    end_time = time.time()
    print('Time taken:', str(end_time - start_time) + 's')

    try:
        with open(file_name, 'wb') as file:
            pickle.dump(database, file)

        print('database saved as:', file_name)
    except pickle.UnpicklingError as e:
        print('failed to save database:', file_name)

    return database

def make_from(img, folder, amountx, amounty, use_repeat=True):

    width, height = img.size

    chunk_width = math.ceil(width / amountx)
    chunk_height = math.ceil(height / amounty)

    total_chunks =  math.ceil(width / chunk_width) *  math.ceil(height / chunk_height)

    print('result dimension:', width, height)
    print('total chunks:', total_chunks)
    print('repeat:', use_repeat)

    if chunk_width < 1 or chunk_height < 1:
        raise ValueError('width or height for each small piece of images is less than 1px:', width, height, '/', amountx, amounty)

    database = _load_database(folder, chunk_width, chunk_height, repeat)

    chunk_count = 0
    background = Image.new('RGB', img.size, 'black')
    print('building image from database ...')
    for h in range(0, height, chunk_height):
        for w in range(0, width, chunk_width):
            btmx = w + chunk_width
            btmy = h + chunk_height
            curr_chunk = img.crop((w, h, btmx, btmy))
            best_match = database.find_closest(curr_chunk)
            background.paste(best_match.img, (w, h))
            if not use_repeat:
                database.remove(best_match) # remove used images
            chunk_count += 1
            print('\r >>>', chunk_count, '/' , total_chunks, '=> {}%'.format(math.ceil(chunk_count / total_chunks * 100)),  end='')
    print(' done')

    return background


def main():

    parser = argparse.ArgumentParser(description='build image from images')
    parser.add_argument('source', help='the image to stimulate')
    parser.add_argument('folder', help='the folder containing images used to stimulate the source')
    parser.add_argument('destination', help='the base name of the output file, not including extension')
    parser.add_argument('amountx', type=int, help='the number of pieces to break down width')
    parser.add_argument('amounty', type=int, help='the number of pieces to break down height')
    parser.add_argument('-r', '--repeat', action='store_true', help='allow build with repeating images')
    args = parser.parse_args()

    input_file = args.source
    output_file = args.destination + '{}.jpg'
    database_folder = args.folder
    src = Image.open(input_file)
    background = make_from(src, database_folder, args.amountx, args.amounty, use_repeat=args.repeat)
    background.save(args.destination + '_background_{}.jpg'.format('repeat' if repeat else 'no_repeat'))
    for blend_percent in range(0, 10):
        blend_percent = blend_percent / 10
        image = Image.blend(src, background, blend_percent)
        image.save(output_file.format(blend_percent))
    print('done =>', output_file)

if __name__ == '__main__':
    main()
