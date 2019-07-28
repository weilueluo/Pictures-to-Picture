

from items import ImageDatabase
folder = '_img'


def save():
    global folder
    database = ImageDatabase(40, 40, folder)
    database.process_and_save_files()


def load():
    database = ImageDatabase.load(folder, 40, 40)
    print(database.width)
    print(database.height)
    print(len(database.files))
    print(len(database.images))


def main():
    # save()
    load()


if __name__ == '__main__':
    main()