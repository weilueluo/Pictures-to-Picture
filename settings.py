



ORIGINAL_IMAGE_SIZE_FACTOR = 1

ALLOW_USE_EXISING_IF_SEEM_SAME = True

MIN_ITEMS_PER_THREAD = 10

MAX_THREAD_PER_PROCESS = 1

MAX_CHUNKS_USE = None  # or int

COLOR_DIFF_METHOD = 'euclidean'
"""
'color space'  # very fast but not accurate at all
'euclidean' 
'euclidean optimized'  # slightly better than euclidean but much slower

# not implemented yet
'cie76'
'cie94'
'ciede2000'
'cmc'
"""
# XXX if change variables below, it will re-create your database

IMAGES_FOLDER = 'images'
DATABASE_FILE = 'database'
POSTFIX = 'data'

DATABASE_FOLDER = '{folder}.' + POSTFIX

MAX_CACHE_PROCESSED_IMAGES = 2000

DATABASE_IMAGE_HEIGHT = 100
DATABASE_IMAGE_WIDTH = 100
