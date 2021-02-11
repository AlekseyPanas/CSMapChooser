import pygame
import random
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


class MapTile:
    CANCEL_COLOR = (210, 0, 0)
    SET_COLOR = (0, 190, 0)

    def __init__(self, map_name):
        self.map = map_name
        self.revealed = False
        self.color = MapTile.SET_COLOR

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
        for tile in [t for t in [tiles[(self_idx % 3) + (i * 3)] for i in list(range(h)) if (self_idx % 3) + (i * 3) < len(tiles)]
                     if t != self]:
            for letter in set(self.map.lower()):
                if letter != " " and letter in tile.map.lower():
                    col_count += 1

        self.row = row_count
        self.col = col_count

    def __repr__(self):
        return self.map


def get_eliminatables(map_tiles, length):
    choices = []
    for _ in range(length):
        valid = False
        while not valid:
            choice = random.choice(map_tiles)
            if not choice in choices:
                choices.append(choice)
                valid = True

    return choices


SCREEN_SIZE = (600, 600)
screen = pygame.display.set_mode([SCREEN_SIZE[0], SCREEN_SIZE[1] + cscale(100)], pygame.DOUBLEBUF)

map_names = ["Dust II", "Mirage", "Cache", "Inferno", "Overpass", "Nuke", "Train", "Vertigo", "Agency", "Office", "Anubis"]
map_tiles = [MapTile(name) for name in map_names]
random.shuffle(map_tiles)

eliminatable_maps_length = 4
eliminatable_maps = get_eliminatables(map_tiles, eliminatable_maps_length)

width = 3
height = round(len(map_names) / 3)
square_dim = SCREEN_SIZE[1] // max(width, height)

arial_font = pygame.font.SysFont("Arial", cscale(32))
arial_font_small = pygame.font.SysFont("Arial", cscale(18))
arial_font_medium = pygame.font.SysFont("Arial", cscale(25))
ELIMINATE_TEXT = arial_font_small.render("ELIMINATING", True, (0, 0, 0))

hidden_square = pygame.Surface([square_dim for _ in range(2)]).convert_alpha()
hidden_square.fill((115, 115, 115))
pygame.draw.rect(hidden_square, (0, 0, 0), pygame.Rect((0, 0), (square_dim, square_dim)), cscale(10))

revealed_square = pygame.Surface([square_dim for _ in range(2)], pygame.SRCALPHA, 32).convert_alpha()
pygame.draw.rect(revealed_square, (0, 0, 0), pygame.Rect((0, 0), (square_dim, square_dim)), cscale(10))

shift = [(SCREEN_SIZE[0] - width * square_dim) / 2, (SCREEN_SIZE[1] - height * square_dim) / 2]

# Sets rows and columns for all tiles
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
                if 0 <= event.pos[0] - shift[0] <= width * square_dim and 0 <= event.pos[1] - shift[1] <= height * square_dim:
                    idx = int(((event.pos[1] - shift[1]) // square_dim) * 3 + (event.pos[0] - shift[0]) // square_dim)
                    if idx < len(map_tiles) and not map_tiles[idx].revealed:
                        map_tiles[idx].revealed = True
                        if map_tiles[idx] in eliminatable_maps:
                            map_tiles[idx].color = MapTile.CANCEL_COLOR
                        eliminatable_maps = get_eliminatables(map_tiles, eliminatable_maps_length)

    for i in range(len(map_tiles)):
        top_left = (shift[0] + (i % 3) * square_dim, shift[1] + (i // 3) * square_dim)
        center = [pos + square_dim / 2 for pos in top_left]

        if not map_tiles[i].revealed:

            screen.blit(hidden_square, top_left)
        else:
            rendered_text = arial_font.render(map_tiles[i].map, True, map_tiles[i].color)
            screen.blit(rendered_text, rendered_text.get_rect(center=center))

            row_text = arial_font_small.render("row: " + str(map_tiles[i].row), True, (110, 0, 180))
            col_text = arial_font_small.render("col: " + str(map_tiles[i].col), True, (0, 110, 180))
            screen.blit(row_text, row_text.get_rect(center=[center[0] - square_dim / 4, center[1] + square_dim / 3]))
            screen.blit(col_text, col_text.get_rect(center=[center[0] + square_dim / 4, center[1] + square_dim / 3]))

            screen.blit(revealed_square, top_left)

    rendered_eliminating_maps = arial_font_medium.render(", ".join([t.map for t in eliminatable_maps]), True, (200, 0, 0))
    screen.blit(ELIMINATE_TEXT, ELIMINATE_TEXT.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] + cscale(15))))
    screen.blit(rendered_eliminating_maps, rendered_eliminating_maps.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] + cscale(55))))

    # Update Display
    pygame.display.update()
