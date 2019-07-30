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
            # try to load files existing database
            print('Attempting to load database from folder: {}'.format(database_folder))
            existing_database = ImageDatabase.load(folder, size, size)

            number_of_images_in_existing_database = len(existing_database.images)

            if not repeat and number_of_images_in_existing_database < pieces_required:
                raise ValueError('Existing database does not contain enough pictures: {} < {}'.format(
                    number_of_images_in_existing_database, pieces_required))

            number_of_images_in_specified_folder = len(glob(folder + '/*[jpg|png]'))

            #
            # if number of images are the same then high chance database is unchanged,
            # return if settings allowed to return
            #
            if number_of_images_in_existing_database == number_of_images_in_specified_folder \
                    and settings.ALLOW_USE_EXISING_IF_SEEM_SAME:
                # print('Existing database seem to be coherent {} == {}'.format(number_of_images_in_specified_folder,
                #                                                               number_of_images_in_existing_database))
                return existing_database
            # ask if they want to use the existing database if reached here
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

        except pickle.PicklingError:  # raise when failed checking before loading database
            print('Failed to load existing database: {}'.format(database_folder))
        except ValueError as e:  # raise by internal checking
            print(e)
        except EOFError:  # raise when loading fails
            print('Data is corrupted in existing database {}'.format(database_folder))

    #
    # database folder does not exists or user wants to create new database if reached here
    #
    print('Creating new database from folder: {}'.format(folder))

    database = ImageDatabase(size, size, folder)

    #
    # checks before actually process the image files found
    #
    files_found = len(database.files)

    if not repeat and pieces_required > files_found:
        raise ValueError(
            'Number of pictures in folder {} is not enough: {} < {}'.format(folder, files_found, pieces_required))

    if settings.MAX_CHUNKS_USE:
        limited_pieces = settings.MAX_CHUNKS_USE * settings.MAX_CACHE_PROCESSED_IMAGES
        if not repeat and pieces_required > limited_pieces:
            raise ValueError(
                'Number of pictures limited {} is not enough: {} < {}, try to increase settings.MAX_CHUNKS_USE'.format(
                    folder, limited_pieces, pieces_required))

    # now actually process the files
    database.process_and_save_files()

    # finished
    return database


def make_from(source, folder, size, factor, use_repeat=True):
    src_width, src_height = source.size
    width = int(src_width * factor)
    height = int(src_height * factor)
    source = source.resize((width, height))

    pieces_required = math.ceil(width / size) * math.ceil(height / size)

    print('=' * 50)
    print('factor:', factor)
    print('result dimension:', width, height)
    print('total pieces:', pieces_required)
    print('repeat:', use_repeat)
    print('algorithm:', settings.COLOR_DIFF_METHOD)
    print('=' * 50)

    if size < 1 or size < 1:
        raise ValueError('width or height for each small piece of images is less than 1px: {} {} < {}'.format(
            width, height, size))

    database = _load_database(folder, size, use_repeat, pieces_required)
    database.process_images()

    print('=' * 50)
    print('Database size:', database.size)
    print('=' * 50)

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
            best_match = database.find_closest(curr_chunk, use_repeat, method=settings.COLOR_DIFF_METHOD)
            background.paste(best_match, (w, h))
            chunk_count += 1
            utilities.print_progress(chunk_count, pieces_required)
    utilities.print_done(time.time() - start_time)

    return source, background


def main():
    parser = argparse.ArgumentParser(description='build image from images')
    parser.add_argument('-src', '--source', help='the image to stimulate')
    parser.add_argument('-s', '--size', type=int, help='the size of each pieces')
    parser.add_argument('-f', '--folder', help='the folder containing images used to stimulate the source')
    parser.add_argument('-d', '--dest', help='the base name of the output file, not including extension')
    parser.add_argument('-r', '--repeat', action='store_true', help='allow build with repeating images')
    parser.add_argument('-fa', '--factor', type=int, help='result size factor compared to original')
    args = parser.parse_args()

    input_file = args.source
    database_folder = args.folder
    src = Image.open(input_file).convert('RGB')
    source, background = make_from(src, database_folder, args.size, args.factor, use_repeat=args.repeat)

    print('Blending & saving images ... ')

    folder = args.dest
    if not os.path.isdir(folder):
        os.mkdir(folder)

    background_file = folder + '/background_{}.jpg'
    background.save(background_file.format('repeat' if args.repeat else 'no_repeat'))

    output_file = folder + '/{}.jpg'
    blend_range = 10
    for index, blend_percent in enumerate(range(0, blend_range)):
        blend_percent = blend_percent / blend_range
        image = Image.blend(source, background, blend_percent)
        image.save(output_file.format(blend_percent))
        utilities.print_progress(index+1, blend_range)
    utilities.print_done(folder)


if __name__ == '__main__':
    main()
