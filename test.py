import sys

from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')


from glob import glob





def center_crop(img, new_width, new_height):
    width, height = img.size
    if width < new_width or height < new_height:
        raise ValueError('width/height must not less than new width/new height for cropping:', width, '<', new_width, 'or', height, '<', new_height)
    topy = (height - new_height) / 2
    topx = (width - new_width) / 2
    btmx = width - topx
    btmy = height - topy
    return img.crop((topx,topy,btmx,btmy))


def trim_to_ratio(img, width_ratio, height_ratio):
    width, height = img.size
    if width < width_ratio or height < height_ratio:
        raise ValueError('width/height must not less than width ratio/ height ratio for trimming:', width, '<', width_ratio, 'or', height, '<', height_ratio)

    width_factor = width / width_ratio
    height_factor = height / height_ratio

    if height_factor < width_factor:
        width = int(height / height_ratio * width_ratio)
        return center_crop(img, width, height)
    else:
        height = int(width / width_ratio * height_ratio)
        return center_crop(img, width, height)

class Image_:

    def __init__(self, image, width, height):
        if isinstance(image, Image.Image):
            self.img = image
        else:
            img = Image.open(image).convert('RGB')
            self.img = img.resize((width, height))
        self.avg_r, self.avg_g, self.avg_b = self._get_avg(self.img)

    def _get_avg(self, img):
        width, height = img.size
        r_sum = 0
        b_sum = 0
        g_sum = 0
        total = 0
        for w in range(0, width):
            for h in range(0, height):
                r,g,b = img.getpixel((w, h))
                r_sum += r
                b_sum += b
                g_sum += g
                total += 1
        r_avg = r_sum // total
        b_avg = b_sum // total
        g_avg = g_sum // total

        return (r_avg, g_avg, b_avg)


from itertools import repeat
class ImageDatabase:
    def __init__(self, folder, size):
        self.size = size
        width = self.size[0]
        height = self.size[1]
        pics_files = glob(folder + '/*[jpg|png]')
        print('pics found:', len(pics_files))
        self.imgs = list(map(Image_, pics_files, repeat(width), repeat(height)))
        print('self.imgs:', len(self.imgs))

    def sort_by_avg_rgb(img):
        sum = pow(img.avg_r - ImageDatabase.curr_other.avg_r, 2) + pow(img.avg_b - ImageDatabase.curr_other.avg_g, 2) + pow(img.avg_b - ImageDatabase.curr_other.avg_b, 2)
        return pow(sum, 0.5)


    def find_closest(self, other):
        other = Image_(other, self.size[0], self.size[1])
        ImageDatabase.curr_other = other
        self.imgs.sort(key=ImageDatabase.sort_by_avg_rgb)
        print('len:', len(self.imgs), end='')
        return self.imgs[0]

    def remove(self, img):
        self.imgs.remove(img)

import math
def test(img, amountx, amounty):
    folder = 'pixiv_img'
    width, height = img.size
    chunk_width = math.ceil(width / amountx)
    chunk_height = math.ceil(height / amounty)
    # print('each chunk:', chunk_width, chunk_height)
    if chunk_width < 1 or chunk_height < 1:
        raise ValueError('width or height for each chunk is less than 1:', width, height)

    chunksize = (chunk_width, chunk_height)
    print('Generating database from folder:', folder)
    database = ImageDatabase(folder, (chunk_width, chunk_height))

    chunks = []
    chunk_count = 0
    background = Image.new('RGB', img.size, 'white')
    print('Generating image from database')
    for h in range(0, height, chunk_height):
        for w in range(0, width, chunk_width):
            print('\r', w, h, '=>', width, height, end='')
            btmx = w + chunk_width
            btmy = h + chunk_height
            # print(w,h,btmx,btmy)
            curr_chunk = img.crop((w, h, btmx, btmy))
            chunks.append(curr_chunk)
            chunk_count += 1
            # curr_chunk.save('chunks/chunk_'+ str(chunk_count) + '.jpg')
            best_match = database.find_closest(curr_chunk)
            background.paste(best_match.img, (w, h))
            database.remove(best_match)
    print('\rDone')
    return background


def main():
    src = Image.open('img/pic.png')
    background = test(src, 30, 40)
    image = Image.blend(src, background, 0.60)
    image.save('output.jpg')

if __name__ == '__main__':
    main()
