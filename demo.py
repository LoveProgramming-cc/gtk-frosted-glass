#!/usr/bin/env python3
"""A window with a frosted bar across the top and a frosted pill, over a scrolling grid.

    python3 demo.py                 # run it; scroll the grid under the bar
    python3 demo.py --png out.png   # draw the window to a PNG and quit (for checking)
"""
import colorsys
import os
import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, GLib, Gtk  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from glass import GlassOverlay  # noqa: E402

CSS = """
/* What is blurred has to be opaque: a blurred picture with holes lets the sharp one show. */
.under { background: @view_bg_color; }

/* The glass itself: a translucent wash; glass.py draws the blur under it. */
.bar { background: alpha(@view_bg_color, 0.74); }
.bar headerbar { background: none; box-shadow: none; }
.bar .title { font-size: 2em; font-weight: 800; margin: 0 24px 14px 24px; }
.pill {
  background: alpha(@popover_bg_color, 0.72);
  color: @popover_fg_color;
  border-radius: 18px;
  padding: 5px 7px;
  box-shadow: 0 6px 20px alpha(black, 0.10), 0 1px 3px alpha(black, 0.12), 0 0 0 1px alpha(black, 0.05);
}
.tile { border-radius: 10px; min-width: 150px; min-height: 190px; }
"""


def tiles():
    flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, valign=Gtk.Align.START, homogeneous=True,
                       max_children_per_line=8, column_spacing=18, row_spacing=18,
                       margin_start=24, margin_end=24, margin_bottom=24)
    rules = []
    for i in range(48):
        r, g, b = colorsys.hsv_to_rgb(i * 0.137 % 1, 0.55, 0.9)
        rules.append('.t%d { background: rgb(%d,%d,%d); }' % (i, r * 255, g * 255, b * 255))
        tile = Gtk.Label(label=str(i + 1))
        tile.add_css_class('tile')
        tile.add_css_class('t%d' % i)
        tile.add_css_class('title-1')
        flow.append(tile)
    return flow, '\n'.join(rules)


def build(app):
    flow, tile_css = tiles()
    provider = Gtk.CssProvider()
    provider.load_from_string(CSS + tile_css)
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                              Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    scroller = Gtk.ScrolledWindow(child=flow, hscrollbar_policy=Gtk.PolicyType.NEVER)
    scroller.add_css_class('under')
    overlay = GlassOverlay(child=scroller, backing='view_bg_color')

    # A bar across the top. It is in the overlay, not above the list, so the list goes under it.
    bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.START)
    bar.add_css_class('bar')
    bar.append(Adw.HeaderBar(show_title=False))
    title = Gtk.Label(label='Frosted glass', xalign=0)
    title.add_css_class('title')
    bar.append(title)
    # The list starts below the bar, however tall the bar turns out to be.
    overlay.add_glass(bar, radius=0, blur=38, on_height=lambda h: flow.set_margin_top(int(h) + 10))

    # A small pill floating at the bottom.
    pill = Gtk.Box(halign=Gtk.Align.CENTER, valign=Gtk.Align.END, margin_bottom=18, spacing=2)
    pill.add_css_class('pill')
    for name in ('edit-undo-symbolic', 'edit-redo-symbolic', 'document-edit-symbolic', 'edit-delete-symbolic'):
        button = Gtk.Button(icon_name=name)
        button.add_css_class('flat')
        pill.append(button)
    overlay.add_glass(pill, radius=18, blur=22)

    window = Adw.ApplicationWindow(application=app, default_width=900, default_height=640, title='Frosted glass')
    window.set_content(overlay)
    window.present()
    return window, scroller


def save_png(window, scroller, path, app):
    def scroll():
        scroller.get_vadjustment().set_value(150)
        return False

    def save():
        snap = Gtk.Snapshot.new()
        Gtk.WidgetPaintable.new(window).snapshot(snap, window.get_width(), window.get_height())
        window.get_renderer().render_texture(snap.to_node(), None).save_to_png(path)
        app.quit()
        return False

    GLib.timeout_add(1200, scroll)
    GLib.timeout_add(2200, save)


def main():
    png = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == '--png' else None
    app = Adw.Application(application_id='io.github.frostedglass.Demo')

    def activate(app):
        window, scroller = build(app)
        if png:
            save_png(window, scroller, png, app)

    app.connect('activate', activate)
    return app.run(sys.argv[:1])


if __name__ == '__main__':
    sys.exit(main())
