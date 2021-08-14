import pygame
from enum import IntEnum
import random
import math
import const


class Object:
    def __init__(self, lifetime, pos, z_order, tags):
        self.lifetime = lifetime
        self.kill = False

        # Draw order
        self.z_order = z_order

        # Set of string tags that can identify an object
        self.tags = set(tags)

        # Center position of object
        self.pos = list(pos)

        # Separate physics from appearance
        self.render_body = None
        self.physics_body = None

        # Integer identification of object
        self.id = -1

    def set_id(self, id):
        self.id = id

    @staticmethod
    def rotate(image, rect, angle):
        """Rotate the image while keeping its center."""
        # Rotate the original image without modifying it.
        new_image = pygame.transform.rotate(image, angle).convert_alpha()
        # Get a new rect with the center of the old rect.
        rect = new_image.get_rect(center=rect.center)
        return new_image, rect

    def run_sprite(self, screen, game):
        self.render(screen, game)
        self.update(screen, game)

    def render(self, screen, game):
        pass

    def update(self, screen, game):
        pass


class Tile(Object):

    SHADOW_SHIFT = 2
    # Gives the percent margin of the tile width based on how many colors need to fit in the bar
    MARGIN_PERCENT_FUNCTION = lambda num_colors: abs(-(math.atan(num_colors-4))*9+14) / 100
    COLOR_BAR_SHIFT_FROM_CENTER_PERCENT = 0.35
    COLOR_TEXT_SHIFT_FROM_CENTER_PERCENT = 0.2
    PERCENT_COLOR_CIRCLE_WIDTH = 0.12
    WORD_WIDTH_PERCENT = 0.9
    MAX_FONT_SIZE_PERCENT = 0.25

    class TILE_TYPES(IntEnum):
        MAP = 0
        HELPER = 1

    def __init__(self, tile_type, tile_width, word, pos, game):
        super().__init__(-1, pos, 1, {"tile"})

        # String contents of the tile
        self.word = word
        # Tile type
        self.tile_type = tile_type

        self.tile_width = tile_width

        # If map tile...
        self.is_eliminated = False

        # Is the tile revealed
        self.is_revealed = False

        # Sets physics body
        self.physics_body = pygame.Rect(0, 0, tile_width, tile_width)
        # Sets render body
        self.render_body = pygame.Surface((tile_width, tile_width)).convert_alpha()



        # Gets all colors within this tile's word
        self.all_colors = const.remove_dupes_keep_order(list([i for i in [game.get_letter_color(letter) for letter in self.word] if i != -1]))

        if self.tile_type == Tile.TILE_TYPES.HELPER and random.randint(1, 5) == 5:
            self.reveal(game)

        # Generates word
        max_font_size = Tile.MAX_FONT_SIZE_PERCENT * self.tile_width

        constant_font_size = 5
        constant_word_width = const.get_word_font(constant_font_size).size(self.word)[0]

        desired_word_width = self.tile_width * Tile.WORD_WIDTH_PERCENT
        # Performs ratio to find desired font size
        desired_font_size = (desired_word_width * constant_font_size) / constant_word_width
        desired_font_size = desired_font_size if desired_font_size < max_font_size else max_font_size

        font = const.get_word_font(desired_font_size)

        self.rendered_word_black = font.render(self.word, True, (0, 0, 0))
        # Creates colored version of word
        self.rendered_word_color = pygame.Surface((self.rendered_word_black.get_width(),
                                                   self.rendered_word_black.get_height()),
                                                  pygame.SRCALPHA, 32).convert_alpha()
        # Tracks cursor position
        cur_pos = 0
        # Blits each letter in a different color
        for letter in self.word:
            # Gets color
            col = game.get_letter_color(letter)
            # If character isn't a letter, turns it black
            if col == -1:
                col = (0, 0, 0)
            else:
                col = col.rgb
            # Draws letter
            self.rendered_word_color.blit(font.render(letter, True, col), (cur_pos, 0))
            # Shifts cursor
            cur_pos += font.size(letter)[0]*0.99

        # Generates color circle display bar
        color_circle_width = Tile.PERCENT_COLOR_CIRCLE_WIDTH * self.tile_width
        if len(self.all_colors) == 1:
            self.color_surf = pygame.Surface((color_circle_width, color_circle_width), pygame.SRCALPHA, 32).convert_alpha()
            pygame.draw.circle(self.color_surf, self.all_colors[0].rgb, (color_circle_width/2,
                                                                         color_circle_width/2),
                               color_circle_width / 2)
        else:
            spread_width = self.tile_width - (Tile.MARGIN_PERCENT_FUNCTION(len(self.all_colors)) * self.tile_width) * 2
            all_color_circle_width = color_circle_width * len(self.all_colors)
            gap_width = (spread_width - all_color_circle_width) / (len(self.all_colors) - 1)
            self.color_surf = pygame.Surface((spread_width, color_circle_width), pygame.SRCALPHA, 32).convert_alpha()
            for i in range(len(self.all_colors)):
                pygame.draw.circle(self.color_surf, self.all_colors[i].rgb,
                                   ((color_circle_width / 2) + ((gap_width+color_circle_width) * i),
                                    color_circle_width / 2), color_circle_width / 2)

    def render(self, screen, game):
        # Accounts for shadow shift
        actual_tile_center = (self.pos[0] + (1 if self.is_revealed else -1) * Tile.SHADOW_SHIFT,
                              self.pos[1] + (1 if self.is_revealed else -1) * Tile.SHADOW_SHIFT)

        # Shadow DUDES
        pygame.draw.rect(screen, (110, 110, 110) if self.is_revealed else (70, 70, 70),
                         self.render_body.get_rect(center=(self.pos[0] + (-1 if self.is_revealed else 1) * Tile.SHADOW_SHIFT,
                                                           self.pos[1] + (-1 if self.is_revealed else 1) * Tile.SHADOW_SHIFT)), border_radius=10)

        # Actual tile BG
        if not self.is_revealed:
            col = (130, 130, 130)
        elif self.tile_type != Tile.TILE_TYPES.MAP:
            col = (180, 180, 180)
        elif self.is_eliminated:
            col = (180, 150, 150)
        else:
            col = (150, 180, 150)
        pygame.draw.rect(screen, col, self.render_body.get_rect(center=actual_tile_center), border_radius=10)

        # Text
        if self.is_revealed:
            screen.blit(self.rendered_word_color,
                        self.rendered_word_color.get_rect(
                            center=(actual_tile_center[0],
                                    actual_tile_center[1]-(Tile.COLOR_TEXT_SHIFT_FROM_CENTER_PERCENT*self.tile_width))))
            screen.blit(self.rendered_word_black, self.rendered_word_black.get_rect(center=actual_tile_center))

        # Color info display
        screen.blit(self.color_surf,
                    self.color_surf.get_rect(center=(actual_tile_center[0],
                                                     actual_tile_center[1] + Tile.COLOR_BAR_SHIFT_FROM_CENTER_PERCENT*self.tile_width)))

    def reveal(self, game):
        if not self.is_revealed:
            self.is_revealed = True
            game.update_revealed_letters(self.word)
            game.do_update_displays = True
            game.newly_revealed_tile = self

    def update(self, screen, game):
        self.physics_body.center = self.pos

        for event in game.events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT and self.physics_body.collidepoint(event.pos):
                self.reveal(game)



"""
- Each hidden tile shows all colors contained within the letters of its word
- Each row and column shows the remaining # of letters belonging to each color that have not been revealed
- At the bottom, all colors are shown along with the revealed letters. Question mark tells you if more letters of that
color exist. No question mark means all letters of that color have already been shown
- List shows all the revealed and hidden words
- Tiles can either be green for selected maps, red for eliminated maps, or gray for helper words
- Elimination method from last game transfers
- Annotation feature
"""