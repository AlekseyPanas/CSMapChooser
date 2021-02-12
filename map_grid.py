import pygame
import random
import copy
import math

pygame.init()


# Scales a set of coordinates to the current screen size based on a divisor factor
def cscale(*coordinate, divisor=600):
    if len(coordinate) > 1:
        return tuple([int(coordinate[x] / divisor * SCREEN_SIZE[x % 2]) for x in range(len(coordinate))])
    else:
        return int(coordinate[0] / divisor * SCREEN_SIZE[0])


# Scales a set of coordinates to the current screen size based on a divisor factor. Doesn't return integers
def posscale(*coordinate, divisor=600):
    if len(coordinate) > 1:
        return tuple([coordinate[x] / divisor * SCREEN_SIZE[x] for x in range(len(coordinate))])
    else:
        return coordinate[0] / divisor * SCREEN_SIZE[0]


def get_helper_string(length_lower_bound=4, length_upper_bound=7):
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    return "".join([random.choice(alphabet) for _ in range(random.randint(length_lower_bound, length_upper_bound))])


def get_eliminatables(map_tiles, length):
    choices = []
    for _ in range(length):
        valid = False
        while not valid:
            choice = random.choice(map_tiles)
            if choice not in choices and choice.map in eliminatable:
                choices.append(choice)
                valid = True

    return choices


def get_common_letter_count(word1, word2):
    count = 0
    for letter in set(word1.lower()):
        if letter in word2.lower():
            count += 1
    return count


class MapTile:
    CANCEL_COLOR = (210, 0, 0)
    SET_COLOR = (0, 190, 0)
    HELPER_COLOR = (25, 50, 200)

    def __init__(self, map_name):
        self.map = map_name
        self.revealed = False if self.map in eliminatable else True
        self.color = MapTile.SET_COLOR if self.map in eliminatable else MapTile.HELPER_COLOR

        # Counts how many common letters in row and column
        self.row = 0
        self.col = 0

    def set_row_and_col(self, w, h, self_idx, tiles):
        slices = [(self_idx // w) * w, ((self_idx // w) + 1) * w]
        if slices[1] > len(tiles):
            slices[1] = len(tiles)

        # Counts how many map names in the same row have a common letter
        row_count = 0
        for tile in [t for t in tiles[slices[0]: slices[1]] if t != self]:
            for letter in set(self.map.lower()):
                if letter != " " and letter in tile.map.lower():
                    row_count += 1

        # Same for columns
        col_count = 0
        for tile in [t for t in
                     [tiles[(self_idx % w) + (i * w)] for i in list(range(h)) if (self_idx % w) + (i * w) < len(tiles)]
                     if t != self]:
            for letter in set(self.map.lower()):
                if letter != " " and letter in tile.map.lower():
                    col_count += 1

        self.row = row_count
        self.col = col_count

    def __repr__(self):
        return self.map


# SCREEN SIZE
SCREEN_SIZE = (600, 600)
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.DOUBLEBUF)

SHOW_SIDEBAR = True

# Names of all tiles
map_names = ["Dust II", "Mirage", "Cache", "Inferno", "Overpass", "Nuke", "Train", "Vertigo", "Agency", "Office",
             "Anubis"]
# Actual CSGO maps to differentiate from helper strings
eliminatable = copy.copy(map_names)

# Adds helper strings (initially revealed tiles to help figure out where maps are)
helper_string_count = 9
map_names += [get_helper_string() for _ in range(helper_string_count)]

# Creates tiles and shuffles them
map_tiles = [MapTile(name) for name in map_names]
random.shuffle(map_tiles)

# Each turn, how many maps should be chosen as possible for elimination
eliminatable_maps_length = 4
eliminatable_maps = get_eliminatables(map_tiles, eliminatable_maps_length)

# Width and height of tile grid, as well as the square side length of each tile
width = 4
height = math.ceil(len(map_names) / width)
square_dim = SCREEN_SIZE[1] // max(width, height)

# Fonts and pre-rendered text
arial_font = pygame.font.SysFont("Arial", cscale(32))
arial_font_small = pygame.font.SysFont("Arial", cscale(18))
arial_font_medium = pygame.font.SysFont("Arial", cscale(25))
ELIMINATE_TEXT = arial_font_small.render("ELIMINATING", True, (0, 0, 0))

# Generates right sidebar with map helper
rendered_names = [arial_font_small.render(m, True, (255, 0, 255)) for m in map_names]
max_name_length = max([surf.get_width() for surf in rendered_names])

common_counts = [[get_common_letter_count(word1, word2) if word2 != word1 else "-" for word2 in map_names] for word1 in map_names]
rendered_counts = [[arial_font_small.render(str(cnt), True, (min(200 - i * 5, 255), min(160 - i * 5, 255), min(50 + i * 5, 255))) for cnt in cnt_arr] for i, cnt_arr in enumerate(common_counts)]

count_width = rendered_counts[0][0].get_width() * 2

padding = cscale(5)
sidebar_width = int(max_name_length + count_width * len(rendered_counts) * 2.1 + padding * len(rendered_counts))
sidebar_height = rendered_names[0].get_height() * len(rendered_names) + padding * 2

sidebar_surface = pygame.Surface((sidebar_width, sidebar_height), pygame.SRCALPHA, 32).convert_alpha()

for i in range(len(rendered_names)):
    sidebar_surface.blit(rendered_names[i], (padding, padding + i * rendered_names[0].get_height()))

for cnt_arr_id in range(len(rendered_counts)):
    for cnt_id in range(len(rendered_counts[cnt_arr_id])):
        sidebar_surface.blit(rendered_counts[cnt_arr_id][cnt_id],
                             (padding * 3 + max_name_length + cnt_arr_id * count_width * padding * .5,
                              padding + cnt_id * rendered_names[0].get_height()))

# Creates screen
screen = pygame.display.set_mode([SCREEN_SIZE[0] + (sidebar_width if SHOW_SIDEBAR else 0), SCREEN_SIZE[1] + cscale(100)], pygame.DOUBLEBUF)

# Pre-made tile box surfaces
hidden_square = pygame.Surface([square_dim for _ in range(2)]).convert_alpha()
hidden_square.fill((115, 115, 115))
pygame.draw.rect(hidden_square, (0, 0, 0), pygame.Rect((0, 0), (square_dim, square_dim)), cscale(10))

revealed_square = pygame.Surface([square_dim for _ in range(2)], pygame.SRCALPHA, 32).convert_alpha()
pygame.draw.rect(revealed_square, (0, 0, 0), pygame.Rect((0, 0), (square_dim, square_dim)), cscale(10))

# The offset from the top left corner of the screen where to start drawing the grid (centers it)
shift = [(SCREEN_SIZE[0] - width * square_dim) / 2, (SCREEN_SIZE[1] - height * square_dim) / 2]

# Sets rows and columns for all tiles
# Each row and column value tells you how many common letters there are in all the maps in the same row
for i in range(len(map_tiles)):
    map_tiles[i].set_row_and_col(width, height, i, map_tiles)

running = True
while running:
    # Clear Screen
    screen.fill((200, 200, 200))

    # Event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                # If the click is within the grid range
                if 0 <= event.pos[0] - shift[0] <= width * square_dim and 0 <= event.pos[1] - shift[1] <= height * square_dim:

                    # Gets the grid index of the click
                    idx = int(
                        ((event.pos[1] - shift[1]) // square_dim) * width + (event.pos[0] - shift[0]) // square_dim)

                    # If the click wasn't on a nonexistent tile (out of range) or on an open tile
                    if idx < len(map_tiles) and not map_tiles[idx].revealed:

                        # Reveals tile
                        map_tiles[idx].revealed = True

                        # If map was queued to be eliminated, set it to cancelled mode
                        if map_tiles[idx] in eliminatable_maps:
                            map_tiles[idx].color = MapTile.CANCEL_COLOR

                        # Creates new set of eliminating maps for next round
                        eliminatable_maps = get_eliminatables(map_tiles, eliminatable_maps_length)

    for i in range(len(map_tiles)):

        # Gets the top left corner and center of the current tile being drawn
        top_left = (shift[0] + (i % width) * square_dim, shift[1] + (i // width) * square_dim)
        center = [pos + square_dim / 2 for pos in top_left]

        # Draws tile square if tile is hidden
        if not map_tiles[i].revealed:
            screen.blit(hidden_square, top_left)

        # Otherwise, Draws map name in its respective color as well as the row and column values
        else:
            rendered_text = arial_font.render(map_tiles[i].map, True, map_tiles[i].color)
            screen.blit(rendered_text, rendered_text.get_rect(center=center))

            row_text = arial_font_small.render("row: " + str(map_tiles[i].row), True, (110, 0, 180))
            col_text = arial_font_small.render("col: " + str(map_tiles[i].col), True, (0, 110, 180))
            screen.blit(row_text,
                        row_text.get_rect(center=[center[0] - square_dim / height, center[1] + square_dim / width]))
            screen.blit(col_text,
                        col_text.get_rect(center=[center[0] + square_dim / height, center[1] + square_dim / width]))

            screen.blit(revealed_square, top_left)

    # Draws text displaying the next eliminating maps at the bottom
    rendered_eliminating_maps = arial_font_medium.render(", ".join([t.map for t in eliminatable_maps]), True,
                                                         (200, 0, 0))
    screen.blit(ELIMINATE_TEXT, ELIMINATE_TEXT.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] + cscale(15))))
    screen.blit(rendered_eliminating_maps,
                rendered_eliminating_maps.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] + cscale(55))))

    # blits sidebar
    if SHOW_SIDEBAR:
        screen.blit(sidebar_surface, (SCREEN_SIZE[0], 0))

    # Update Display
    pygame.display.update()
