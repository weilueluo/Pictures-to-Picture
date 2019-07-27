

from items import ImageDatabase
import settings


def main():
    folder = '_img'
    database = ImageDatabase.load(settings.DATABASE_FOLDER.format(folder=folder))
    print(database.width)
    print(database.height)
    print(database.files_size)
    print(database.images_size)

if __name__ == '__main__':
    main()