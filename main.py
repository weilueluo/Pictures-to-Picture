

import argparse
import sys
from items import ImageDatabase
from PIL import Image
import settings
import os
import pickle
from glob import glob
import math
import time
import utilities

sys.stdout.reconfigure(encoding='utf-8')


def _load_database(folder, size, repeat, pieces_required):

    database_folder = utilities.get_database_structure(folder).folder

    # first, try load from existing database if exists
    if os.path.isdir(database_folder) and (
            size < settings.DATABASE_IMAGE_WIDTH or size < settings.DATABASE_IMAGE_HEIGHT):
        try:
            # try to load existing database
            print('Attempting to load database from folder: {}'.format(database_folder))
            existing_database = ImageDatabase.load(folder, size, size)

            number_of_images_in_existing_database = len(existing_database.images)

            if not repeat and number_of_images_in_existing_database < pieces_required:
                raise ValueError('Existing database does not contain enough pictures: {} < {}'.format(
                    number_of_images_in_existing_database, pieces_required))

            number_of_images_in_specified_folder = len(glob(folder + '/*[jpg|png]'))

            if number_of_images_in_existing_database == number_of_images_in_specified_folder \
                    and settings.ALLOW_USE_EXISING_IF_SEEM_SAME:
                print('Existing database seem to be coherent {} == {}'.format(number_of_images_in_specified_folder,
                                                                              number_of_images_in_existing_database))
                return existing_database
            # ask if they want to use the existing database
            while True:
                ans = input('Existing database found with size requirement satisfied, ' + os.linesep +
                            'existing database:{}, specified folder:{}, use existing? [y/n]:'.format(
                                number_of_images_in_existing_database,
                                number_of_images_in_specified_folder))
                if ans == 'y':
                    return existing_database
                elif ans == 'n':
                    break
                print('Please give answer as \'y\' or \'n\'')

        except pickle.PicklingError:
            print('Failed to load existing database: {}'.format(database_folder))
        except ValueError as e:
            print(e)

    #
    # database folder does not exists or user wants to create new database
    #
    print('Creating new database from folder: {}'.format(folder))

    database = ImageDatabase(size, size, folder)

    files_found = len(database.files)

    if not repeat and pieces_required > files_found:
        raise ValueError('Number of pictures in folder {} is not enough: {} < {}'.format(folder, files_found, pieces_required))

    start_time = time.time()
    database.process_and_save_files()
    end_time = time.time()
    print('Time taken:', str(end_time - start_time) + 's')

    return database


def make_from(source, folder, size, use_repeat=True):

    width, height = source.size
    pieces_required = math.ceil(width / size) * math.ceil(height / size)

    print('result dimension:', width, height)
    print('total pieces:', pieces_required)
    print('repeat:', use_repeat)

    if size < 1 or size < 1:
        raise ValueError('width or height for each small piece of images is less than 1px: {} {} < {}'.format(
            width, height, size))

    database = _load_database(folder, size, use_repeat, pieces_required)

    chunk_count = 0
    background = Image.new(source.mode, source.size, 'black')
    print('building image from database ...')
    start_time = time.time()
    for h in range(0, height, size):
        for w in range(0, width, size):
            btmx = w + size
            btmy = h + size
            if btmx > width:
                btmx = width
            if btmy > height:
                btmy = height
            curr_chunk = source.crop((w, h, btmx, btmy))
            best_match = database.find_closest(curr_chunk)
            background.paste(best_match.img, (w, h))
            if not use_repeat:
                # remove used images
                database.remove(best_match)
            chunk_count += 1
            print('\r >>>', chunk_count, '/' , pieces_required, '=> {}%'.format(math.ceil(chunk_count / pieces_required * 100)),  end='')
    print(' done: {}s'.format(time.time() - start_time))

    return background


def main():

    parser = argparse.ArgumentParser(description='build image from images')
    parser.add_argument('source', help='the image to stimulate')
    parser.add_argument('size', type=int, help='the size of each pieces')
    parser.add_argument('folder', help='the folder containing images used to stimulate the source')
    parser.add_argument('dest', help='the base name of the output file, not including extension')
    parser.add_argument('-r', '--repeat', action='store_true', help='allow build with repeating images')
    args = parser.parse_args()

    input_file = args.source
    database_folder = args.folder
    source = Image.open(input_file).convert('RGB')
    background = make_from(source, database_folder, args.size, use_repeat=args.repeat)

    print('Blending & saving images ...')

    folder = args.dest
    if not os.path.isdir(folder):
        os.mkdir(folder)

    background_file = folder + '/background_{}.jpg'
    background.save(background_file.format('repeat' if args.repeat else 'no_repeat'))

    output_file = folder + '/{}.jpg'
    for blend_percent in range(0, 10):
        blend_percent = blend_percent / 10
        image = Image.blend(source, background, blend_percent)
        image.save(output_file.format(blend_percent))
        print('\r {}'.format(blend_percent), end='')
    print(' done =>', folder)


if __name__ == '__main__':
    main()
