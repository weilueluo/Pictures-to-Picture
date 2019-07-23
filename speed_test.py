from PIL import Image

import time


def test_getdata(im):
    start = time.time()
    bands = im.getdata()
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
    end = time.time()
    print('test getdata:', end - start, 's')
    return r_avg, g_avg, b_avg

import itertools
def test_getdata2(im):
    start = time.time()
    bands = im.getdata()
    bands_sum = [sum(x) for x in itertools.izip(*bands)]
    r_sum = bands_sum[0]
    g_sum = bands_sum[1]
    b_sum = bands_sum[2]
    total = len(bands)
    r_avg = r_sum // total
    g_avg = g_sum // total
    b_avg = b_sum // total
    end = time.time()
    print('test getdata2:', end - start, 's')
    return r_avg, g_avg, b_avg

def test_getpixel(im):
    start = time.time()
    width, height = im.size
    r_sum = 0
    b_sum = 0
    g_sum = 0
    total = 0
    for w in range(0, width):
        for h in range(0, height):
            r,g,b = im.getpixel((w, h))
            r_sum += r
            b_sum += b
            g_sum += g
            total += 1
    r_avg = r_sum // total
    b_avg = b_sum // total
    g_avg = g_sum // total
    end = time.time()
    print('test getpixel:', end - start, 's')
    return r_avg, g_avg, b_avg


class test:
    def __init__(self, a , b):
        print('from ab')
    def __init__(self, a,b,c):
        print('from abc')



def main():
    # im = Image.open('_img/pic.png')
    # for i in range(0,3):
    #     print('test',i,'='*20)
    #     print(test_getdata(im))
    #     # print(test_getpixel(im))
    #     print(test_getdata2(im))

if __name__ == '__main__':
    main()
