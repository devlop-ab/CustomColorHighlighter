import re
import os
import time
import zlib
import math
import struct
import threading
import colorsys
from functools import partial

import sublime
import sublime_plugin

from .settings import Settings, SettingTogglerCommandMixin
from .colorizer import SchemaColorizer

# if $$highlighter$$ is colored in this comment
# then no colors have been configured

NAME = "Custom Highlighter"
VERSION = "1.0.0"

regex_cache = None
re_cache = None

fallback_colors = {
    "$$highlighter$$": "#ffd700", # fallback placeholder
}

def regex_factory():
    global regex_cache

    if regex_cache != None:
        colors_regex, colors_regex_capture = regex_cache
    else:
        colors = settings.get('colors', {})

        if not colors:
            colors = fallback_colors

        print({
            "colors": colors,
        })

        colors_regex = r'(%s)' % r'(?<![-.\w])%s(?![-.\w])' % r'(?![-.\w])|(?<![-.\w])'.join(map(lambda key: re.escape(key), colors.keys()))

        # print({
        #     "colors_regex": colors_regex,
        # })

        # colors_regex = []

        # if simple_colors:
            # colors_regex = r'(%s)' % colors_regex

        # colors_regex = r'|'.join(colors_regex)

        colors_regex_capture = r'\1'

        # if len(colors_regex):
        #     colors_regex_capture = r'|\1'
        # else:
            # colors_regex_capture = ''

        regex_cache = colors_regex, colors_regex_capture

    # print({
    #     "regex_cache": regex_cache,
    # })

    return colors_regex, colors_regex_capture


def re_factory():
    global re_cache

    if re_cache != None:
        colors_re, colors_re_capture = re_cache
    else:
        colors_regex, colors_regex_capture = regex_factory()
        colors_re = re.compile(colors_regex)
        colors_re_capture = re.sub(r'\\([0-9])', lambda m: chr(int(m.group(1))), colors_regex_capture)

        re_cache = colors_re, colors_re_capture

    return colors_re, colors_re_capture


# Full PNG is: PNG_HEAD + PNG_IHDR + PNG_IDAT[mode] + PNG_IEND
PNG_HEAD = b'\x89PNG\r\n\x1a\n'
PNG_IHDR = b'\x00\x00\x00\x0dIHDR\x00\x00\x00 \x00\x00\x00 \x08\x06\x00\x00\x00szz\xf4'
PNG_IDAT = {
    'circle': b'\x00\x00\x01\x13IDATx\x9c\xed\xd6\xc1\r\xc3 \x0c@QX!g\xa4\x8c\xd0\x11:BF\xe8\x01q\xee\x1c\xdd\x82e2\x00\xb30\x00\xb5U#U\x11\x85`\xac\xe6\xc2\xe1_\xc3K\x93\xd8U)%ue\x97\x1e>\x01\x13P\x05\xac\xb7{)\x03Y\xc8C\x01\x8a\xdb\xe3\x89\x05\xc8C\x162\x90:6\n\xd0\x90\x83v(}\x07\x17?\xb6C\x0e\xd2R\x80\x05z\x1d\x0f\xae\x00r/h\x19\x05\xe8\xda\xe1\r@F\xe8\x11\x80\xab\x1d~\x02\x90\xe8q\xb0\x00\xa6\xf4\xcc\x19\x00|\'\x0c\x07`[\x87\x9f\x04`\x96\x03\xf0\x82\x00\xcf\x01\x04A@\xe0\x00\xa2  v\x03h\xc25/~\x06\x897\xc3\x01\x04A@\xff#\xa0\xd9.\x05\xe8\x7f\ti\xb1H\x01\xfa?\xc3\xed\xb3\xd5v\x01\x00\x0e\xb3\xfeADK\xc4\t\x00p\x9c\xf7\x8fb\x02hZ(\\\x00.2=\x02\xc0\x96\x1a\xa2q8\xaer5\n\xc8\xbf\x84+\xbd\x13?\x9e\xb9\xcbw.\x05\xc8\x19\xfa:<\xcd\x89H\x133\xd0\xee\xc0\x05f\xd6\xc2\xdf\xb9n\xc0\xbf\x9a\x80\t\xb8\x1c\xf0\x06-\x9f\xcd\xf4\x17\xe9(\x03',
    'square': b'\x00\x00\x00\x4aIDATx\x9c\xed\xceA\r\x00 \x0cC\xd19A\x02\x12\x90\x80\x04$\xe0\xff\xd49 =\xb1,\xf9\x87\x7fm_H\x8a\xcaJ\xcf\x01\x00x\x02\xc6\\r\xda\xe7Z\x01\x00\x00\x00@?\x80;\xecB\x01\x00\x00\x00\xa0\x1f\xe0W\x00\x00\x94\x03\x12\\\xf0$\x87\xd4i\x0c\x98',
    'fill': b'\x00\x00\x00\x40IDATx\x9c\xed\xcf1\x11\x00 \x10\x03\xc1w\x82\x04$ \x01\tH\xc0\x7f\x05"R|\xb3\xc5\xb5\x99M\x8d\xb9^\xd2>7\xaa\x00\x00\x00\x00\x00\x00\x00\xda\x01\xe9@z\x00\x00\x00\x00\x00\x00\x00\xa0\x1d\xf0\x01\xb4]Pj]\x9av\xf7',
}
PNG_IEND = b'\x00\x00\x00\x00IEND\xaeB`\x82'

PNG_RE = re.compile(b'\\x1f\\x2f\\x3f|\\x4f\\x5f\\x6f')
PNG_DATA = {
    'circle': zlib.decompress(PNG_IDAT['circle'][8:-4]),
    'square': zlib.decompress(PNG_IDAT['square'][8:-4]),
    'fill': zlib.decompress(PNG_IDAT['fill'][8:-4]),
}
DEFAULT_GUTTER_ICON = 'circle'


def toicon(name, gutter_icon=True, light=True):
    base_path = os.path.join(sublime.packages_path(), 'User', '%s.cache' % NAME)

    if not os.path.exists(base_path):
        os.mkdir(base_path)

    if gutter_icon not in PNG_DATA:
        gutter_icon = DEFAULT_GUTTER_ICON

    icon_path = os.path.join(base_path, name + '_' + gutter_icon + '.png')

    if not os.path.exists(icon_path):
        r = int(name[4:6], 16)
        g = int(name[6:8], 16)
        b = int(name[8:10], 16)
        a = int(name[10:12] or 'ff', 16) / 255.0
        # print("r={} g={} b={} a={}".format(r, g, b, a))
        if light:
            x = 0xff * (1 - a)
            y = 0xcc * (1 - a)
        else:
            x = 0x99 * (1 - a)
            y = 0x66 * (1 - a)

        r *= a
        g *= a
        b *= a

        # print("x(r={} g={} b={}), y(r={} g={} b={})".format(int(r + x), int(g + x), int(b + x), int(r + y), int(g + y), int(b + y)))
        I1 = lambda v: struct.pack("!B", v & (2**8 - 1))
        I4 = lambda v: struct.pack("!I", v & (2**32 - 1))

        png = PNG_HEAD + PNG_IHDR
        col_map = {
            b'\x1f\x2f\x3f': I1(int(r + x)) + I1(int(g + x)) + I1(int(b + x)),
            b'\x4f\x5f\x6f': I1(int(r + y)) + I1(int(g + y)) + I1(int(b + y)),
        }

        data = PNG_RE.sub(lambda m: col_map[m.group(0)], PNG_DATA[gutter_icon])
        compressed = zlib.compress(data)
        idat = b'IDAT' + compressed
        png += I4(len(compressed)) + idat + I4(zlib.crc32(idat))
        png += PNG_IEND

        with open(icon_path, 'wb') as fp:
            fp.write(png)

    relative_icon_path = os.path.relpath(icon_path, os.path.dirname(sublime.packages_path()))
    relative_icon_path = relative_icon_path.replace('\\', '/')

    return relative_icon_path


# Commands

# class CustomHighlighterCommand(sublime_plugin.WindowCommand):
#     def run_(self, edit_token, args={}):
#         view = self.window.active_view()
#         view.run_command('color_highlight', args)
#
#     def is_enabled(self):
#         return True


class CustomHighlighterEnableLoadSaveCommand(CustomHighlighterCommand):
    def is_enabled(self):
        enabled = super(CustomHighlighterEnableLoadSaveCommand, self).is_enabled()

        if enabled:
            if settings.get('highlight') == 'load-save':
                return False

        return enabled


class CustomHighlighterEnableSaveOnlyCommand(CustomHighlighterCommand):
    def is_enabled(self):
        enabled = super(CustomHighlighterEnableSaveOnlyCommand, self).is_enabled()

        if enabled:
            if settings.get('highlight') == 'save-only':
                return False

        return enabled


class CustomHighlighterDisableCommand(CustomHighlighterCommand):
    def is_enabled(self):
        enabled = super(CustomHighlighterDisableCommand, self).is_enabled()

        if enabled:
            if settings.get('highlight') is False:
                return False

        return enabled


class CustomHighlighterEnableCommand(CustomHighlighterCommand):
    def is_enabled(self):
        view = self.window.active_view()

        if view:
            if settings.get('highlight') is not False:
                return False

        return True


# command to restore color scheme
class CustomHighlighterRestoreCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        erase_highlight_colors()
        colorizer.restore_color_scheme()


all_regs = []


class CustomHighlighterCommand(sublime_plugin.TextCommand):
    '''command to interact with linters'''

    def __init__(self, view):
        self.view = view
        self.help_called = False

    def run_(self, edit_token, args={}):
        '''method called by default via view.run_command;
           used to dispatch to appropriate method'''

        action = args.get('action', '')
        if not action:
            return

        lc_action = action.lower()

        print({
            "lc_action": lc_action,
        })

        if lc_action == 'reset':
            self.reset()
        elif lc_action == 'off':
            self.off()
        elif lc_action == 'on':
            self.on()
        elif lc_action == 'load-save':
            self.enable_load_save()
        elif lc_action == 'save-only':
            self.enable_save_only()
        else:
            highlight_colors(self.view)

    def reset(self):
        '''Removes existing lint marks and restores user settings.'''
        erase_highlight_colors()
        TIMES.clear()
        colorizer.setup_color_scheme(self.view.settings())
        queue_highlight_colors(self.view, preemptive=True)

    def on(self):
        '''Turns background linting on.'''
        settings.set('highlight', True)
        settings.save()
        queue_highlight_colors(self.view, preemptive=True)

    def enable_load_save(self):
        '''Turns load-save linting on.'''
        settings.set('highlight', 'load-save')
        settings.save()
        erase_highlight_colors()

    def enable_save_only(self):
        '''Turns save-only linting on.'''
        settings.set('highlight', 'save-only')
        settings.save()
        erase_highlight_colors()

    def off(self):
        '''Turns background linting off.'''
        settings.set('highlight', False)
        settings.save()
        erase_highlight_colors()


class CustomHighlighterViewEventListener(sublime_plugin.ViewEventListener):
    def on_modified(self):
        if settings.get('highlight') is not True:
            return

        action = self.view.command_history(0, True)[0]
        if action == 'revert':
            erase_highlight_colors()
            queue_highlight_colors(self.view, preemptive=True)
        else:
            selection = action != 'paste'
            queue_highlight_colors(self.view, preemptive=selection, selection=selection)

    def on_close(self):
        vid = self.view.id()
        if vid in TIMES:
            del TIMES[vid]
        if vid in CUSTOM_HIGHLIGHTS:
            del CUSTOM_HIGHLIGHTS[vid]

    def on_activated(self):
        if self.view.file_name() is None:
            return
        vid = self.view.id()
        if vid in TIMES:
            return
        TIMES[vid] = 100

        if settings.get('highlight') in (False, 'save-only'):
            return

        queue_highlight_colors(self.view, preemptive=True)

    def on_post_save(self):
        if settings.get('highlight') is False:
            return

        queue_highlight_colors(self.view, preemptive=True)

    def on_selection_modified(self):
        delay_queue(1000)  # on movement, delay queue (to make movement responsive)


TIMES = {}  # collects how long it took the color highlight to complete
CUSTOM_HIGHLIGHTS = {}  # Highlighted regions


def erase_highlight_colors(view=None):
    if view:
        vid = view.id()
        if vid in CUSTOM_HIGHLIGHTS:
            for name in CUSTOM_HIGHLIGHTS[vid]:
                view.erase_regions(name)
                view.erase_regions(name + '_icon')
        CUSTOM_HIGHLIGHTS[vid] = set()
    else:
        for window in sublime.windows():
            for view in window.views():
                erase_highlight_colors(view)


def highlight_colors(view, selection=False, **kwargs):
    view_settings = view.settings()
    colorizer.setup_color_scheme(view_settings)

    vid = view.id()
    start = time.time()

    if len(view.sel()) > 100:
        selection = False

    if selection:
        selected_lines = [ln for r in view.sel() for ln in view.lines(r)]
    elif view.size() > 512000:
        selected_lines = view.lines(view.visible_region())
    else:
        selected_lines = None

    words = {}
    found = []
    if selected_lines:
        colors_re, colors_re_capture = re_factory()
        matches = [colors_re.finditer(view.substr(l)) for l in selected_lines]
        matches = [
            (
                sublime.Region(
                    selected_lines[i].begin() + m.start(),
                    selected_lines[i].begin() + m.end()
                ),
                m.groups()
            ) if m else (None, None)
            for i, am in enumerate(matches) for m in am
        ]
        matches = [
            (
                rg,
                ''.join(
                    gr[ord(g) - 1] or '' if ord(g) < 10 else g for g in colors_re_capture
                )
            )
            for rg, gr in matches if rg
        ]
        if matches:
            ranges, found = zip(*[q for q in matches if q])
        else:
            ranges = []
    else:
        colors_regex, colors_regex_capture = regex_factory()
        # print({
        #     "colors_regex_a": colors_regex,
        #     "colors_regex_capture": colors_regex_capture,
        # })
        ranges = view.find_all(colors_regex, 0, colors_regex_capture, found)

    # print({
    #     'found': found,
    # })

    colors = settings.get('colors', {})

    if not colors:
        colors = fallback_colors

    print({
        "colors": colors,
    })

    for i, col in enumerate(found):
        # mode, _, col = col.partition('|')
        # print(col)
        # col = col.rstrip(',')
        # print(col)
        # col = col.split(',')
        # print(mode, _, col)

        try:
            # In the form of: black, #FFFFFFFF
            # col0 = col[0]
            # col0 = all_names_to_hex.get(col0.lower(), col0.upper())

            color = colors[col].upper()

            # print({col: color})

            if len(color) == 4: #abc
                color = '#' + color[1] * 2 + color[2] * 2 + color[3] * 2 + 'FF'
            elif len(color) == 5: #abcd
                color = '#' + color[1] * 2 + color[2] * 2 + color[3] * 2 + color[4] * 2
            elif len(color) == 7: #aabbcc
                color += 'FF'

            if re.match(r'^#[A-F0-9]{8}$', color) == None:
                raise ValueError('Invalid color format "%s"' % color)
        # except (ValueError, IndexError, KeyError) as e:
        except (KeyError, ValueError) as e:
            # print({
            #     type(e): e,
            # })
            continue

        # Fix case when color it's the same as background color:
        if hasattr(view, 'style'):
            bg_col = (view.style()['background'] + 'FF')[:9].upper()
            if col == bg_col:
                br = int(bg_col[1:3], 16)
                bg = int(bg_col[3:5], 16)
                bb = int(bg_col[5:7], 16)
                ba = int(bg_col[7:9], 16)
                br += -1 if br > 1 else 1
                bg += -1 if bg > 1 else 1
                bb += -1 if bb > 1 else 1
                col = '#%02X%02X%02X%02X' % (br, bg, bb, ba)

        # print(colorizer)

        name = colorizer.add_color(col, colors)

        # print({
        #     "name": name,
        # })
        if name not in words:
            words[name] = [ranges[i]]
        else:
            words[name].append(ranges[i])

    colorizer.update(view)

    if selected_lines:
        if vid not in CUSTOM_HIGHLIGHTS:
            CUSTOM_HIGHLIGHTS[vid] = set()
        for name in CUSTOM_HIGHLIGHTS[vid]:
            ranges = []
            affected_line = False
            for _range in view.get_regions(name):
                _line_range = False
                for _line in selected_lines:
                    if _line.contains(_range):
                        _line_range = True
                        break
                if _line_range:
                    affected_line = True
                else:
                    ranges.append(_range)
            if affected_line or name in words:
                if name not in words:
                    words[name] = ranges
                else:
                    words[name].extend(ranges)
    else:
        erase_highlight_colors(view)
    all_regs = CUSTOM_HIGHLIGHTS[vid]

    highlight_values = bool(settings.get('highlight_values', True))
    gutter_icon = settings.get('gutter_icon', True)

    for name, w in words.items():
        # print(name, w)
        if highlight_values:
            view.add_regions(name, w, name, flags=sublime.PERSISTENT)

        if gutter_icon:
            wi = [sublime.Region(i, i) for i in set(view.line(r).a for r in w)]
            view.add_regions(name + '_icon', wi, '%sgutter' % colorizer.prefix, icon=toicon(name, gutter_icon=gutter_icon), flags=sublime.PERSISTENT)

        all_regs.add(name)

    if not selection:
        TIMES[vid] = (time.time() - start) * 1000  # Keep how long it took to do a full color highlight
        # print('highlight took %s' % TIMES[vid])


################################################################################
# Queue connection

QUEUE = {}  # views waiting to be processed by Color Highlight

# For snappier color highlighting, different delays are used for different color highlighting times:
# (color_highlighting_time, (delay, delay_when_busy))
DELAYS = (
    (50, (50, 100)),
    (100, (100, 300)),
    (200, (200, 500)),
    (400, (400, 1000)),
    (600, (600, 1500)),
    (800, (800, 2000)),
    (1200, (1200, 1000)),
    (1600, (1600, 3000)),
)


def get_delay(t, view):
    delays = 0

    for _t, d in DELAYS:
        if _t <= t:
            delays = d
        else:
            break

    delays = delays or DELAYS[0][1]

    # If the user specifies a delay greater than the built in delay,
    # figure they only want to see marks when idle.
    min_delay = int(settings.get('delay', 0) * 1000)

    return (min_delay, min_delay) if min_delay > delays[1] else delays


def _update_view(view, filename, **kwargs):
    # It is possible that by the time the queue is run,
    # the original file is no longer being displayed in the view,
    # or the view may be gone. This happens especially when
    # viewing files temporarily by single-clicking on a filename
    # in the sidebar or when selecting a file through the choose file palette.
    valid_view = False
    view_id = view.id()

    if view.is_loading():
        return

    if (view.file_name() or '').encode('utf-8') != filename:
        return

    for window in sublime.windows():
        for v in window.views():
            if v.id() == view_id:
                valid_view = True
                break

    if not valid_view:
        return

    highlight_colors(view, **kwargs)


def queue_highlight_colors(view, delay=-1, preemptive=False, **kwargs):
    '''Put the current view in a queue to be examined by a Color Highlight'''

    if preemptive:
        delay = delay_when_busy = 0
    elif delay == -1:
        delay, delay_when_busy = get_delay(TIMES.get(view.id(), 100), view)
    else:
        delay_when_busy = delay

    kwargs.update({
        'delay': delay,
        'delay_when_busy': delay_when_busy,
        'preemptive': preemptive,
    })

    queue(view, partial(_update_view, view, (view.file_name() or '').encode('utf-8'), **kwargs), kwargs)


def _callback(view, filename, kwargs):
    kwargs['callback'](view, filename, **kwargs)


def background_color_highlight():
    __lock_.acquire()

    try:
        callbacks = list(QUEUE.values())
        QUEUE.clear()
    finally:
        __lock_.release()

    for callback in callbacks:
        sublime.set_timeout(callback, 0)


################################################################################
# Queue dispatcher system:

queue_dispatcher = background_color_highlight
queue_thread_name = 'background color highlight'
MAX_DELAY = 10


def queue_loop():
    '''An infinite loop running the color highlight in a background thread meant to
       update the view after user modifies it and then does no further
       modifications for some time as to not slow down the UI with color highlighting.'''
    global __signaled_, __signaled_first_

    while __loop_:
        # print('acquire...')
        __semaphore_.acquire()
        __signaled_first_ = 0
        __signaled_ = 0
        # print('DISPATCHING!', len(QUEUE))
        queue_dispatcher()


def queue(view, callback, kwargs):
    global __signaled_, __signaled_first_
    now = time.time()
    __lock_.acquire()

    try:
        QUEUE[view.id()] = callback
        delay = kwargs['delay']

        if now < __signaled_ + delay * 4:
            delay = kwargs['delay_when_busy']

        __signaled_ = now
        _delay_queue(delay, kwargs['preemptive'])

        # print('%s queued in %s' % ('' if __signaled_first_ else 'first ', __signaled_ - now))
        if not __signaled_first_:
            __signaled_first_ = __signaled_
    finally:
        __lock_.release()


def _delay_queue(delay, preemptive):
    global __signaled_, __queued_
    now = time.time()

    if not preemptive and now <= __queued_ + 0.01:
        return  # never delay queues too fast (except preemptively)

    __queued_ = now
    _delay = float(delay) / 1000

    if __signaled_first_:
        if MAX_DELAY > 0 and now - __signaled_first_ + _delay > MAX_DELAY:
            _delay -= now - __signaled_first_
            if _delay < 0:
                _delay = 0
            delay = int(round(_delay * 1000, 0))

    new__signaled_ = now + _delay - 0.01

    if __signaled_ >= now - 0.01 and (preemptive or new__signaled_ >= __signaled_ - 0.01):
        __signaled_ = new__signaled_
        # print('delayed to %s' % (preemptive, __signaled_ - now))

        def _signal():
            if time.time() < __signaled_:
                return
            __semaphore_.release()

        sublime.set_timeout(_signal, delay)


def delay_queue(delay):
    __lock_.acquire()
    try:
        _delay_queue(delay, False)
    finally:
        __lock_.release()


# only start the thread once - otherwise the plugin will get laggy
# when saving it often.
__semaphore_ = threading.Semaphore(0)
__lock_ = threading.Lock()
__queued_ = 0
__signaled_ = 0
__signaled_first_ = 0

# First finalize old standing threads:
__loop_ = False
__pre_initialized_ = False


def queue_finalize(timeout=None):
    global __pre_initialized_

    for thread in threading.enumerate():
        if thread.isAlive() and thread.name == queue_thread_name:
            __pre_initialized_ = True
            thread.__semaphore_.release()
            thread.join(timeout)


queue_finalize()

# Initialize background thread:
__loop_ = True
__active_color_highlight_thread = threading.Thread(target=queue_loop, name=queue_thread_name)
__active_color_highlight_thread.__semaphore_ = __semaphore_
__active_color_highlight_thread.start()


################################################################################
# Initialize settings and main objects only once

class CustomHighlighterSettings(Settings):
    def on_update(self):
        window = sublime.active_window()
        view = window.active_view()
        view.run_command('color_highlight', dict(action='reset'))


settings = CustomHighlighterSettings(NAME)

class CustomHighlighterSettingCommand(SettingTogglerCommandMixin, sublime_plugin.WindowCommand):
    settings = settings


if 'colorizer' not in globals():
    colorizer = SchemaColorizer()


################################################################################

def plugin_loaded():
    settings.load()
