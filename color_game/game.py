import pygame
import sprites
import const
import time
import math
import random
import colorsys
from win32api import GetSystemMetrics
import copy


#[print([i*255 for i in colorsys.hsv_to_rgb(*(random.randint(0, 1000) / 1000, 1, 1))]) for i in range(10)]


class Game:
    NUM_COLORS = random.randint(4, 8)
    SPACE_BETWEEN_TILES = 0.1  # As a percent of total tile width
    INITIAL_X_TILE_OFFSET = 20
    INITIAL_Y_TILE_OFFSET = 20
    # What percentage of the defining screen resolution dimension should the tile grid take up
    TILE_PERCENT_OF_SCREEN = 0.55

    # In addition to the grid, how far should the screen extend for additional displays
    EXTEND_RIGHT = 300
    EXTEND_DOWN = 300

    ERASER_RADIUS = 25

    class Color:
        def __init__(self, hsv):
            self.hsv = hsv
            self.rgb = tuple([int(i*255) for i in colorsys.hsv_to_rgb(*self.hsv)])

            self.letters = ""
            self.revealed_letters = ""

        def assign_letter(self, letter):
            if len(letter) == 1:
                self.letters += letter
            else:
                print("Failed to add letter")
                return -1

        def reveal_letters(self, chars):
            print(chars, self.letters, self.revealed_letters)
            for c in list(set(chars)):
                if c.lower() in self.letters and c.lower() not in self.revealed_letters:
                    self.revealed_letters += c.lower()

        def __repr__(self):
            return str((self.rgb, self.letters))

    def __init__(self, maps, grid_dims=(6, 5), word_gen_func=const.get_word):
        # Event array
        self.events = []

        # Game run flag
        self.running = True

        # Function used to generate helper words
        self.word_gen_fun = word_gen_func

        # Tile Grid Dimensions
        self.grid_dims = grid_dims
        total_tiles = self.grid_dims[0] * self.grid_dims[1]

        # Calculates tile width based on monitor size
        screen_dimensions = GetSystemMetrics(0), GetSystemMetrics(1)

        # If the full-fill tile width for the width of the screen causes it to exceed vertically, then the vertical
        # screen dimension is the one that should be used to determine screen size
        if (screen_dimensions[0] / self.grid_dims[0]) * self.grid_dims[1] > screen_dimensions[1]:
            tile_width = (Game.TILE_PERCENT_OF_SCREEN * screen_dimensions[1]) / self.grid_dims[1]
        else:
            tile_width = (Game.TILE_PERCENT_OF_SCREEN * screen_dimensions[0]) / self.grid_dims[0]

        self.tile_width = int(tile_width)

        # Cuts the map list if there are more maps than available tiles
        if len(maps) > total_tiles:
            maps = maps[:total_tiles]
            words = list(maps)
        elif len(maps) < total_tiles:
            words = list(maps) + [word_gen_func() for _ in range(total_tiles - len(maps))]
        else:
            words = list(maps)
        random.shuffle(words)

        # All words and maps
        self.words = words
        self.maps = maps

        # Game window
        self.screen = pygame.display.set_mode(
            (int(self.tile_width * self.grid_dims[0] * (1 + Game.SPACE_BETWEEN_TILES)) + Game.EXTEND_RIGHT + Game.INITIAL_X_TILE_OFFSET,
             int(self.tile_width * self.grid_dims[1] * (1 + Game.SPACE_BETWEEN_TILES)) + Game.EXTEND_DOWN + Game.INITIAL_Y_TILE_OFFSET),
            pygame.DOUBLEBUF)

        # Array containing all colors
        self.colors = []
        diff_range = const.get_max_diff_range(0.95, Game.NUM_COLORS)
        for _ in range(Game.NUM_COLORS):
            self.colors.append(Game.Color(Game.get_new_color(self.colors, diff_range)))
        self.assign_letters()

        # Generates tiles based on given csgo maps and additional helper words
        self.TILES = [sprites.Tile((sprites.Tile.TILE_TYPES.MAP if (word in maps) else sprites.Tile.TILE_TYPES.HELPER), self.tile_width, word,
                                   (Game.INITIAL_X_TILE_OFFSET + (self.tile_width + (Game.SPACE_BETWEEN_TILES*self.tile_width)) * (idx % self.grid_dims[0]) + self.tile_width/2,
                                    Game.INITIAL_Y_TILE_OFFSET + (self.tile_width + (Game.SPACE_BETWEEN_TILES*self.tile_width)) * (idx // self.grid_dims[0]) + self.tile_width/2), self) for idx, word in enumerate(words)]

        # Prints the % of all tiles which have all the colors on them
        print(str(round((len([t for t in self.TILES if len(t.all_colors) == len(self.colors)]) / len(self.TILES)) * 100, 1)) + "%")

        # Surfaces for other displays
        self.word_list_surface = self.render_word_list()
        self.letter_display_surface = self.render_letter_display()

        # Surface for drawing annotations over the screen
        self.annotation_surf = pygame.Surface((self.screen.get_rect().width, self.screen.get_rect().height), pygame.SRCALPHA, 32).convert_alpha()

        # Set this flag to update the displays
        self.do_update_displays = False
        self.newly_revealed_tile = None

        # Flag to determine if pen is drawing
        self.is_drawing = False
        self.previous_draw_point = [0, 0]
        self.eraser_brush = pygame.Surface((Game.ERASER_RADIUS*2, Game.ERASER_RADIUS*2), pygame.SRCALPHA, 32)
        pygame.draw.circle(self.eraser_brush, (0, 0, 0), (Game.ERASER_RADIUS, Game.ERASER_RADIUS), Game.ERASER_RADIUS)
        self.eraser_brush = self.eraser_brush.convert_alpha()

        self.draw_line_width = 4
        self.draw_color = (255, 0, 0)

        # Map elimination Feature
        #########################

        # Static header text
        self.ELIMINATING_TEXT = const.get_gui_font(self.tile_width / 3).render("FIND:", True, (0, 0, 0))

        # String map choice to be found next
        revealed_maps = [t.word for t in self.TILES if t.tile_type == sprites.Tile.TILE_TYPES.MAP and not t.is_revealed]
        self.map_choice = None

        # Renders it
        self.map_choice_text = None

        # Next map choice does same
        self.map_choice_next = random.choice(revealed_maps)
        self.map_choice_next_text = None
        self.update_map_elimination()

    def update_map_elimination(self):
        revealed_maps = [t.word for t in self.TILES if t.tile_type == sprites.Tile.TILE_TYPES.MAP and not t.is_revealed]

        self.map_choice = self.map_choice_next
        self.map_choice_text = const.get_gui_font(self.tile_width / 3).render(self.map_choice, True, (0, 150, 0))

        # Next map choice does same
        if len(revealed_maps):
            self.map_choice_next = random.choice(revealed_maps)
        else:
            self.map_choice_next = "N/A"

        self.map_choice_next_text = const.get_gui_font(self.tile_width / 4).render(self.map_choice_next, True,
                                                                                     (0, 150, 0)).convert_alpha(pygame.Surface((10, 10), pygame.SRCALPHA, 32))
        # Transparency
        self.map_choice_next_text.fill((0, 150, 0, 100), None, pygame.BLEND_RGBA_MULT)

    def update_revealed_letters(self, word):
        for col in self.colors:
            col.reveal_letters(word)

    @staticmethod
    def get_new_color(colors, diff_range=.1):
        """Gets a new color that has an hsv difference of the given range"""

        # Guilty
        valid = False
        while not valid:
            new_col = (random.randint(0, 1000) / 1000, random.randint(90, 100)/100, random.randint(50, 90)/100)

            # Innocent until proven guilty
            valid = True
            for c in colors:
                # if the color difference is too small, choose another one by setting flag to guilty
                if abs(new_col[0] - c.hsv[0]) < diff_range or new_col[0] > 0.9:
                    valid = False

        return new_col

    def get_letter_color(self, letter):
        for col in self.colors:
            if letter.lower() in col.letters.lower():
                return col
        return -1

    def assign_letters(self):
        alph = [i for i in "abcdefghijklmnopqrstuvwxyz"]
        while 1:
            for col in self.colors:
                rand_letter_idx = random.randint(0, len(alph) - 1)
                col.assign_letter(alph[rand_letter_idx])
                alph.pop(rand_letter_idx)
                if not len(alph):
                    break
            if not len(alph):
                break

    def render_letter_display(self):
        SURF_HEIGHT = Game.EXTEND_DOWN * min(.1*len(self.colors) + 0.3, 1)

        letter_display_surf = pygame.Surface((self.screen.get_width(), SURF_HEIGHT), pygame.SRCALPHA,
                                             32).convert_alpha()

        PER_COLOR_DISPLAY_HEIGHT = SURF_HEIGHT / len(self.colors)
        MARGIN_BETWEEN_COL = 0.05 * PER_COLOR_DISPLAY_HEIGHT  # % of above value
        PER_COLOR_DISPLAY_HEIGHT -= MARGIN_BETWEEN_COL

        COLOR_CIRCLE_RADIUS = PER_COLOR_DISPLAY_HEIGHT / 2

        FONT_SIZE = PER_COLOR_DISPLAY_HEIGHT * 0.9
        FONT = const.get_gui_font(FONT_SIZE)

        y_draw_cursor = 0
        for col in self.colors:
            # Draws circle
            pygame.draw.circle(letter_display_surf, col.rgb, (COLOR_CIRCLE_RADIUS, y_draw_cursor + COLOR_CIRCLE_RADIUS), COLOR_CIRCLE_RADIUS)
            # Draws letters
            if not len(col.revealed_letters):
                letters = "?"
            else:
                letters = "".join([i + (", " if idx < len(col.revealed_letters) - 1 else "") for idx, i in enumerate(col.revealed_letters)]) + (", ?" if len(col.letters) > len(col.revealed_letters) else "")
            rendered = FONT.render(letters, True, col.rgb)

            letter_display_surf.blit(rendered, (COLOR_CIRCLE_RADIUS*2 + 10, y_draw_cursor + rendered.get_height()/2))

            y_draw_cursor += PER_COLOR_DISPLAY_HEIGHT + MARGIN_BETWEEN_COL

        return letter_display_surf.convert_alpha()

    def render_word_list(self):
        # Prepares assets and dimensions
        FONT_SIZE = self.tile_width * 0.25
        FONT = const.get_gui_font(FONT_SIZE)

        title_text = FONT.render("WORDS", True, (0, 0, 0))

        LINE_WIDTH = 3
        LINE_MARGIN = 10

        WORD_MARGIN = 5
        TOTAL_WORD_HEIGHT = sum([FONT.size(t.word)[1] + WORD_MARGIN for t in self.TILES])

        SURFACE_HEIGHT = TOTAL_WORD_HEIGHT + LINE_MARGIN*2 + LINE_WIDTH + title_text.get_height()
        SURFACE_WIDTH = max([FONT.size(t.word)[0] for t in self.TILES])*1.1

        # Generates Surface
        word_list_surf = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT),
                                        pygame.SRCALPHA, 32).convert_alpha()

        # Draws the stuff (Draw cursor tracks draw height)
        draw_cursor = 0
        word_list_surf.blit(title_text, title_text.get_rect(center=(SURFACE_WIDTH/2, title_text.get_height()/2)))
        draw_cursor += title_text.get_height()

        pygame.draw.line(word_list_surf, (0, 0, 0),
                         (0, draw_cursor + LINE_MARGIN), (SURFACE_WIDTH, draw_cursor + LINE_MARGIN), LINE_WIDTH)
        draw_cursor += LINE_MARGIN*2 + LINE_WIDTH

        for tile in self.TILES:
            word_rendering = FONT.render(tile.word, True, (80, 80, 80) if tile.tile_type == sprites.Tile.TILE_TYPES.HELPER else (200, 0, 200), (255, 255, 150) if tile.is_revealed else None)
            word_list_surf.blit(word_rendering,
                                word_rendering.get_rect(center=(SURFACE_WIDTH/2,
                                                                draw_cursor + word_rendering.get_height()/2)))
            draw_cursor += word_rendering.get_height() + WORD_MARGIN

        return word_list_surf.convert_alpha()

    def update_displays(self):
        # Eliminates tile if invalid
        if self.newly_revealed_tile.tile_type == sprites.Tile.TILE_TYPES.MAP:
            if self.newly_revealed_tile.word != self.map_choice:
                self.newly_revealed_tile.is_eliminated = True

        self.word_list_surface = self.render_word_list()
        self.letter_display_surface = self.render_letter_display()
        self.update_map_elimination()

    def run_game(self):
        while self.running:
            if self.do_update_displays:
                self.update_displays()

                self.do_update_displays = False

            # Clears screen
            self.screen.fill((255, 255, 255))

            # Updates events and checks for quit
            self.events = pygame.event.get()
            for event in self.events:
                if event.type == pygame.QUIT:
                    self.running = False
                # Allows brush size changes
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == pygame.BUTTON_WHEELUP:
                        self.draw_line_width = min(self.draw_line_width + 1, 20)
                    elif event.button == pygame.BUTTON_WHEELDOWN:
                        self.draw_line_width = max(self.draw_line_width - 1, 1)

            # Runs tiles and annotations
            for t in self.TILES:
                t.run_sprite(self.screen, self)

            # Eraser Functionality
            if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                pygame.draw.circle(self.screen, (150, 150, 150), pygame.mouse.get_pos(), Game.ERASER_RADIUS, 1)
            else:
                mp = pygame.mouse.get_pos()
                pygame.draw.rect(self.screen, (150, 150, 150), pygame.Rect(mp[0] - self.draw_line_width/2,
                                                                           mp[1] - self.draw_line_width/2,
                                                                           self.draw_line_width,
                                                                           self.draw_line_width), 1)

            if pygame.mouse.get_pressed(3)[0] and pygame.key.get_pressed()[pygame.K_LSHIFT]:
                self.annotation_surf.blit(self.eraser_brush, self.eraser_brush.get_rect(center=pygame.mouse.get_pos()), None, pygame.BLEND_RGBA_SUB)

            # Manages Drawing functionality
            elif pygame.mouse.get_pressed(3)[0]:
                if not self.is_drawing:
                    self.previous_draw_point = pygame.mouse.get_pos()
                else:
                    prev_pt = self.previous_draw_point
                    cur_pt = pygame.mouse.get_pos()

                    pygame.draw.line(self.annotation_surf, self.draw_color, prev_pt, cur_pt, self.draw_line_width)

                    self.previous_draw_point = cur_pt

                self.is_drawing = True
            else:
                self.is_drawing = False

            """ DISPLAY COLORS
            posx = 25
            for c in self.colors:
                pygame.draw.circle(self.screen, c.rgb, (posx, 50), 10)
                posx += 50
            """

            # Displays All Words
            self.screen.blit(self.word_list_surface,
                             self.word_list_surface.get_rect(topleft=(
                                 self.screen.get_width() - self.word_list_surface.get_width() - Game.INITIAL_X_TILE_OFFSET*.25,
                                 Game.INITIAL_Y_TILE_OFFSET)))

            self.screen.blit(self.letter_display_surface, self.letter_display_surface.get_rect(center=(self.screen.get_width()/2,
                                                                                                       self.screen.get_height() - Game.EXTEND_DOWN/2)))

            # Displays eliminating feature
            DIST_FROM_BOTTOM = self.ELIMINATING_TEXT.get_height() + 0.2 * Game.EXTEND_DOWN
            MAP_TEXT_WIDTH = self.map_choice_text.get_width()
            ELIMINATING_TEXT_WIDTH = self.ELIMINATING_TEXT.get_width()
            MARGIN_BETWEEN_TEXT = 0.05 * self.EXTEND_RIGHT

            self.screen.blit(self.ELIMINATING_TEXT, (self.screen.get_width() - MARGIN_BETWEEN_TEXT*2 - ELIMINATING_TEXT_WIDTH - MAP_TEXT_WIDTH,
                                                     self.screen.get_height() - DIST_FROM_BOTTOM))
            self.screen.blit(self.map_choice_text, (self.screen.get_width() - MARGIN_BETWEEN_TEXT - MAP_TEXT_WIDTH,
                                                    self.screen.get_height() - DIST_FROM_BOTTOM))
            self.screen.blit(self.map_choice_next_text, self.map_choice_next_text.get_rect(center=(
                self.screen.get_width() - MARGIN_BETWEEN_TEXT - MAP_TEXT_WIDTH/2,
                self.screen.get_height() - DIST_FROM_BOTTOM / 2
            )))

            # Displays annotations
            self.screen.blit(self.annotation_surf, (0, 0))

            # Changes pen color based on clicked pixel
            for event in self.events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_MIDDLE:
                    sample = self.screen.get_at(event.pos)
                    if sample != (255, 255, 255, 255):
                        self.draw_color = sample

            # Updates display
            pygame.display.update()
