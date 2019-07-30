




ALLOW_USE_EXISING_IF_SEEM_SAME = True

MAX_CHUNKS_USE = None  # or (int) number of chunks to use, each chunk is same as MAX_CACHE_PROCESSED_IMAGES

COLOR_DIFF_METHOD = 'euclidean'
"""
'color space'  # very fast but not accurate
'euclidean'  # classic euclidean algorithm
'euclidean optimized'  # slightly better than euclidean but much slower

# not implemented yet
'cie76'
'cie94'
'ciede2000'
'cmc'
"""
# XXX if change variables below, it may re-create your database

IMAGES_FOLDER = 'images'
DATABASE_FILE = 'database'
POSTFIX = 'data'

DATABASE_FOLDER = '{folder}.' + POSTFIX

MAX_CACHE_PROCESSED_IMAGES = 2000

DATABASE_IMAGE_HEIGHT = 100
DATABASE_IMAGE_WIDTH = 100
