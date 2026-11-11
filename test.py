#!/usr/bin/env python3
"""Checks GlassOverlay on whatever GTK 4 is loaded, using GTK alone (no libadwaita).

    python3 test.py            # prints what it measured; exit status 0 when everything passed

A window is drawn to a picture: its left half black, its right half white, with a glass bar
across the top and a glass pill lower down. The sharp black/white edge must come out
blurred under the bar and under the pill, and sharp everywhere else.
"""
import os
import sys
import tempfile

import cairo
import gi

gi.require_version('Gdk', '4.0')
gi.require_version('Gtk', '4.0')
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from glass import GlassOverlay  # noqa: E402

CSS = """
window { background: #808080; }
.left { background: black; }
.right { background: white; }
.bar { background: none; min-height: 80px; }
.pill { background: none; min-height: 60px; min-width: 300px; border-radius: 18px; }
"""
W, H = 600, 400
BLUR = 22.0


def edge_width(data, stride, y):
    """How many pixels the black/white edge takes to go from 10 % to 90 % on row y."""
    row = [data[y * stride + x * 4 + 1] for x in range(W)]
    lo = next((x for x in range(W) if row[x] > 25), None)
    hi = next((x for x in range(W) if row[x] > 230), None)
    return None if lo is None or hi is None else hi - lo


def main():
    Gtk.init()
    version = '%d.%d.%d' % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    provider = Gtk.CssProvider()
    try:
        provider.load_from_data(CSS.encode())      # before GTK 4.12 (and PyGObject of that time)
    except TypeError:
        provider.load_from_data(CSS, -1)
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                              Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    under = Gtk.Box(homogeneous=True)
    for name in ('left', 'right'):
        half = Gtk.Box(hexpand=True)
        half.add_css_class(name)
        under.append(half)
    overlay = GlassOverlay(child=under, backing='theme_bg_color')
    heights = []
    bar = Gtk.Box(valign=Gtk.Align.START)
    bar.add_css_class('bar')
    overlay.add_glass(bar, radius=0, blur=BLUR, on_height=heights.append)
    pill = Gtk.Box(halign=Gtk.Align.CENTER, valign=Gtk.Align.END, margin_bottom=40)
    pill.add_css_class('pill')
    overlay.add_glass(pill, radius=18, blur=BLUR)

    window = Gtk.Window(child=overlay, default_width=W, default_height=H, decorated=False)
    window.present()
    loop = GLib.MainLoop()
    result = {}

    def measure():
        snap = Gtk.Snapshot.new()
        Gtk.WidgetPaintable.new(overlay).snapshot(snap, W, H)
        texture = window.get_renderer().render_texture(snap.to_node(), None)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'glass.png')
            texture.save_to_png(path)
            image = cairo.ImageSurface.create_from_png(path)
        data, stride = image.get_data(), image.get_stride()
        result['renderer'] = type(window.get_renderer()).__name__
        result['size'] = (image.get_width(), image.get_height())
        result['bar'] = edge_width(data, stride, 40)          # inside the bar (rows 0 to 79)
        result['between'] = edge_width(data, stride, 200)     # no glass here
        result['pill'] = edge_width(data, stride, H - 70)     # inside the pill
        loop.quit()
        return False

    GLib.timeout_add(1200, measure)
    loop.run()

    checks = [
        ('picture is %d x %d' % (W, H), result['size'] == (W, H)),
        ('edge under the bar is blurred (%s px)' % result['bar'], result['bar'] is not None and result['bar'] >= 15),
        ('edge under the pill is blurred (%s px)' % result['pill'], result['pill'] is not None and result['pill'] >= 15),
        ('edge between them is sharp (%s px)' % result['between'], result['between'] is not None and result['between'] <= 2),
        ('bar height was reported (%s)' % heights, heights == [80.0]),
    ]
    print('GTK %s, %s' % (version, result['renderer']))
    for text, ok in checks:
        print('  %s  %s' % ('ok  ' if ok else 'FAIL', text))
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == '__main__':
    sys.exit(main())
