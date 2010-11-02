#!/usr/bin/python2
'''
File: clocklet.py
Author: Nathan Hoad
Description: Clocklet is a plugin used in conjunction with adesklets to
             provide an easily configurable clock widget for your desktop.
Original Date Written: Sometime early 2010, around February-March.
'''

import time
import sys
from os.path import join, dirname

import adesklets

large_text = 'PixelFont/75'
medium_text = 'PixelFont/20'
date_text = 'PixelFont/30'
year_text = 'PixelFont/15'

def get_time(format_text):
    """
    Returns time using format_text as formatter. man strftime for details
    """
    return time.strftime(format_text, time.localtime(time.time()))


def text_size(font, text):
    """Gets the height and width of text using font, in imlib2"""
    font_num = adesklets.load_font(font)
    adesklets.context_set_font(font_num)
    width, height = adesklets.get_text_size(text)
    adesklets.free_font(font_num)
    return width, height


def text_width(font, text):
    """Returns the width of text using font, in imlib2"""
    return text_size(font, text)[0]


def text_height(font, text):
    """Returns the height of text using font, in imlib2"""
    return text_size(font, text)[1]


class Config(adesklets.ConfigFile):
    """
    the default configuration for clocklet.

    color: the color you want your text to be.
    alpha: level of transparency, 0-255
    caps: convert all text to capital letters or leave as is
    displays: the real meat of the applet, it's a tuple of
              maps, here are the expected values in each map:
        format: the time text you want to display (man strftime for details)
        x_pos: the x co-ord you want to draw the text at.
        y_pos: the y co-ord you want to draw the text at.
        font: the font to use for the formatted time.

    please note that the x_pos and y_pos variables can be strings you wish
    to evaluate, or simply numbers. (strings are nice to evaluate as you
    can do functions, to adjust for width changes and the like)
    """
    y_y = "(text_height(medium_text, get_time('%a')) * 2"\
        + " + text_height(date_text, '%d')) - 2"

    p_x = "text_width(large_text, get_time('%l:%M')) - "\
        + "text_width(year_text, get_time('%p')) - 2",
    p_y = "(text_height(medium_text, get_time('%a')) * 2 + "\
        + "text_height(date_text, get_time('%d'))) - 2",

    cfg_default = {
            'color': '#FFFFFF',
            'alpha': 255,
            'caps': True,
            'width': 290,
            'height': 120,
            'displays': (
            {'format': '%l:%M',
                'x_pos': 0,
                'y_pos': 0,
                'font': large_text},
            {'format': '%a',
                'x_pos': "text_width(large_text, get_time('%l:%M'))",
                'y_pos': 5,
                'font': medium_text},
            {'format': '%b',
                'x_pos': "text_width(large_text, get_time('%l:%M'))",
                'y_pos': "text_height(medium_text, get_time('%a')) + 4",
                'font': medium_text},
            {'format': '%d',
                'x_pos': "text_width(large_text, get_time('%l:%M'))",
                'y_pos': "(text_height(medium_text, get_time('%a')) * 2) + 1",
                'font': date_text},
            {'format': '%Y',
                'x_pos': "text_width(large_text, get_time('%l:%M'))",
                'y_pos': y_y,
                'font': year_text},
            {'format': '%p',
                'x_pos': p_x,
                'y_pos': p_y,
                'font': year_text},)}


class Clocklet(adesklets.Events_handler):

    def __init__(self, basedir):
        if len(basedir) == 0:
            self.basedir = '.'
        else:
            self.basedir = basedir
        adesklets.Events_handler.__init__(self)

    def _refresh_buffer(self):
        """
        Makes a nice clean buffer to use
        """
        # free the old buffer
        if self.buffer is not None:
            adesklets.free_image(self.buffer)

        self.buffer = adesklets.create_image(self.sizeX, self.sizeY)
        adesklets.context_set_image(self.buffer)

    def _blend_image(self):
        """
        Blend the buffer image onto the foreground image
        """
        buf_x = adesklets.image_get_width()
        buf_y = adesklets.image_get_height()

        adesklets.context_set_image(0)
        adesklets.context_set_blend(False)
        adesklets.blend_image_onto_image(self.buffer, 1, 0, 0, buf_x, buf_y, \
            0, 0, buf_x, buf_y)
        adesklets.context_set_blend(True)

    def _draw_time(self):
        """
        Draw the time onto the canvas
        """
        x_pos = 0
        y_pos = 0

        # run through the tuple and print each part of the time
        for display in self.displays:
            text = get_time(display['format'])
            if self.caps:
                text = text.upper()
            s_x_pos = display['x_pos']
            s_y_pos = display['y_pos']

            x_pos = eval(s_x_pos) if isinstance(s_x_pos, str) else s_x_pos

            y_pos = eval(s_y_pos) if isinstance(s_y_pos, str) else s_x_pos

            # sure this is gross and dumb, but it's easier.
            cur_font = adesklets.load_font(display['font'])
            adesklets.context_set_font(cur_font)
            adesklets.text_draw(x_pos, y_pos, text)
            adesklets.free_font(cur_font)

    def __del__(self):
        """
        To be called on deletion
        """
        adesklets.Events_handler.__del__(self)

    def ready(self):
        """
        Get everything ready to be drawn
        """
        # load the config, and set the text color and alpha
        self.id = adesklets.get_id()
        self.config = None
        self.buffer = None
        self._get_config()

        adesklets.context_set_color(self.red, self.green,\
            self.blue, self.alpha)

        adesklets.context_set_anti_alias(True)
        adesklets.window_resize(self.sizeX, self.sizeY)
        adesklets.window_set_transparency(True)
        adesklets.window_show()

    def _get_config(self):
        """
        Load up the config file and its values
        """
        if self.config is None:
                self.config = Config(adesklets.get_id(),
                        join(self.basedir, 'config.txt'))

        config = self.config
        color = config.get('color')
        (self.red, self.green, self.blue) = self._parse_color(color)
        self.alpha = config.get('alpha')
        self.displays = config.get('displays')
        self.caps = config.get('caps')
        self.sizeX = config.get('width')
        self.sizeY = config.get('height')

    def alarm(self):
        """
        Draw the shit out of the clock!
        """
        self._refresh_buffer()
        self._draw_time()
        self._blend_image()
        return 58 # refresh every 58 seconds to allow for program slowness

    def _parse_color(self, color):
        """
        Parse an HTML-style hexadecimal color value into respective decimal RGB
        values.
        """

        def hex_color_to_int(color):
            return eval('0x%s' % color)

        color = color[1:] # remove "#" from start of color
        red = hex_color_to_int(color[:2])
        green = hex_color_to_int(color[2:4])
        blue = hex_color_to_int(color[4:])
        return (red, green, blue)


Clocklet(dirname(__file__)).pause()
