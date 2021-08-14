import pygame
import random
import requests
pygame.font.init()

# Loads huge word lib
word_site = "https://www.mit.edu/~ecprice/wordlist.100000"
response = requests.get(word_site)
WORDS = [w.decode("utf-8") for w in response.content.splitlines()]


def get_word():
    return random.choice(WORDS)


def remove_dupes_keep_order(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def load_image(path, size=None):
    img = pygame.image.load(path)
    if size is not None:
        img = pygame.transform.smoothscale(img, (int(size[0]), int(size[1])))
    return img.convert_alpha()


# Scales a set of coordinates to the current screen size based on a divisor factor
def cscale(*coordinate, screen_size, divisor=(1000, 900)):
    if len(coordinate) > 1:
        return tuple([int(coordinate[x] / divisor[x % 2] * screen_size[x % 2]) for x in range(len(coordinate))])
    else:
        return int(coordinate[0] / divisor[0] * screen_size[0])


# Scales a set of coordinates to the current screen size based on a divisor factor. Doesn't return integers
def posscale(*coordinate, screen_size, divisor=(1000, 900)):
    if len(coordinate) > 1:
        return tuple([coordinate[x] / divisor[x % 2] * screen_size[x] for x in range(len(coordinate))])
    else:
        return coordinate[0] / divisor[0] * screen_size[0]


def get_word_font(size):
    return pygame.font.SysFont("Arial", int(size))


def get_gui_font(size):
    return pygame.font.SysFont("Calibri Body", int(size))


def get_max_diff_range(color_range_length, num_colors):
    """# MATH PROBLEM FOR CALCULATING MAX DIFF_RANGE WITHOUT CAUSING A POTENTIAL INFINITE LOOP
    (ie diff_range is basically X/2, since it represents the bounds within which another color cannot be chosen
    L represents the Hue range (colorsys has a range of 0-1, so L=1. N is the number of total colors that need to
    be chosen)

    Given a line segment of length "L", and "N" smaller line segments of equal length, "X", which must fit on the
    larger line segment without overlapping, what is the maximum length of "X" such that if the smaller line
    segments are added to random parts of the larger line segment one by one (assuming the randomization ensures
    no overlap), there is 100% chance that all the smaller line segments will all fit (If "X" is too large, for
    example, there might be a point where if the first few smaller line segments have been randomly distributed
    across the larger line in a highly inefficient manner, the next line segment will not have space to be placed
    without overlap)"""
    # d is a special value which calculates how many intervals to split the # line into to encompass num_colors,
    # since splitting the number line in half repeatedly is the LEAST efficient way to distribute the colors,
    # Thus accounting for the possibility of least efficiency and ensuring its impossible
    def get_d(previous_value, depth, num_cols):
        num = previous_value + (2**depth)
        if num_cols <= num:
            return num
        else:
            return get_d(num, depth + 1, num_cols)
    d = get_d(0, 0, num_colors)
    return (color_range_length / (d+1)) / 2  # diff range is actually half the calculated range, hence /2
