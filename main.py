import sys
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image

class Image_:

    def __init__(self, tuple_of_inputs):
        image = tuple_of_inputs[0]
        width = tuple_of_inputs[1]
        height = tuple_of_inputs[2]
        if isinstance(image, Image.Image):
            self.img = image
        else:
            img = Image.open(image).convert('RGB')
            self.img = img.resize((width, height))
        self.avg_r, self.avg_g, self.avg_b = self._get_avg(self.img)

    def _get_avg(self, img):
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



from glob import glob
from multiprocessing import Pool
import os, time
from itertools import repeat

class ImageDatabase:
    def __init__(self, folder, size):
        print('Creating database from folder:', folder)
        # width and height for each images in this database
        self.width = size[0]
        self.height = size[1]
        self.files = glob(folder + '/*[jpg|png]')
        self.imgs = []
        self.curr_sort_object = None
        print('Pictures found:', self.files_size)

    def _sort_by_avg_rgb_diff(img):
        # https://en.wikipedia.org/wiki/Color_difference
        # Euclidean Formula
        sum = pow(img.avg_r - ImageDatabase.curr_sort_object.avg_r, 2) \
            + pow(img.avg_g - ImageDatabase.curr_sort_object.avg_g, 2) \
            + pow(img.avg_b - ImageDatabase.curr_sort_object.avg_b, 2)
        return pow(sum, 0.5)


    def generate_images(self):
        print('Processing Pictures found ...')
        cpus = os.cpu_count()
        total_files = self.files_size
        chunksize = total_files // cpus ** 2
        if chunksize < cpus:
            chunksize = 1
        pool = Pool(processes=cpus)
        for index, item in enumerate(pool.imap_unordered(Image_, zip(self.files, repeat(self.width), repeat(self.height)), chunksize)):
            print('\r >>> {} / {} => {}%'.format(index, total_files, math.ceil((index / total_files) * 100)), end='')
            self.imgs.append(item)
        print(' done')

    def find_closest(self, other):
        other = Image_((other, self.width, self.height))
        ImageDatabase.curr_sort_object = other
        self.imgs.sort(key=ImageDatabase._sort_by_avg_rgb_diff)
        return self.imgs[0]

    def remove(self, img):
        self.imgs.remove(img)

    @property
    def files_size(self):
        return len(self.files)


import math
def make_from(img, folder, amountx, amounty):
    width, height = img.size
    total_chunks = amountx * amounty
    print('result dimension:', width, height)
    print('total chunks:', total_chunks)
    chunk_width = math.ceil(width / amountx)
    chunk_height = math.ceil(height / amounty)
    if chunk_width < 1 or chunk_height < 1:
        raise ValueError('width or height for each small piece of images is less than 1px:', width, height, '/', amountx, amounty)


    database = ImageDatabase(folder, (chunk_width, chunk_height))

    files_found = database.files_size
    if total_chunks > files_found:
        raise ValueError('size of database is not enough:', total_chunks, '>', files_found)

    if total_chunks > files_found / 2:
        print('database is small for', total_chunks, 'pieces:', files_found, 'may get bad result')


    start_time = time.time()
    database.generate_images()
    end_time = time.time()
    print('Time taken:', str(end_time - start_time) + 's')

    chunk_count = 0
    background = Image.new('RGB', img.size, 'black')
    print('Creating image from database')
    for h in range(0, height, chunk_height):
        for w in range(0, width, chunk_width):
            btmx = w + chunk_width
            btmy = h + chunk_height
            curr_chunk = img.crop((w, h, btmx, btmy))
            chunk_count += 1
            best_match = database.find_closest(curr_chunk)
            background.paste(best_match.img, (w, h))
            database.remove(best_match)
            print('\r >>>', chunk_count, '/' ,total_chunks, '=> {}%'.format(math.ceil(chunk_count / total_chunks * 100)),  end='')
    print(' done')
    return background


def main():
    input_file = 'pic.jpg'
    output_file = 'output{}.jpg'
    database_folder = 'imgs'
    src = Image.open(input_file)
    background = make_from(src, database_folder, 60, 80)
    background.save('background.jpg')
    for blend_percent in range(0, 10):
        blend_percent = blend_percent / 10
        image = Image.blend(src, background, blend_percent)
        image.save(output_file.format(blend_percent))
    print('done =>', output_file)

if __name__ == '__main__':
    main()
