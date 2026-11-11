"""Frosted glass for GTK 4: bars that float over a view show it blurred through them.

GTK 4.22 and later can do this alone, with the CSS property backdrop-filter; this
is for apps that also have to run on older GTK 4, whose CSS has none. The overlay
that holds the bars draws the glass:
the view underneath is recorded once as a render node, and drawn a second time,
blurred and clipped to the bar's shape, behind each bar added as glass. The
bar's own translucent CSS background is the wash over the blur.

    overlay = GlassOverlay(child=scrolled_view, backing='view_bg_color')
    overlay.add_glass(pill, radius=18, blur=22)

Copyright © 2026 the Inkpad authors. MIT licence; see LICENSE.
"""
from gi.repository import GLib, Graphene, Gsk, Gtk


class GlassOverlay(Gtk.Overlay):
    """A Gtk.Overlay whose glass children are frosted over its main child.

    backing: the name of a theme colour (such as 'view_bg_color') that the view under the
    glass is filled with. It is taken to go on past the edges of the view, so that a bar at
    the edge does not fade out. Leave it None when nothing is at an edge.
    """

    __gtype_name__ = 'FrostedGlassOverlay'

    def __init__(self, backing=None, **properties):
        super().__init__(**properties)
        self.backing = backing
        self._glass = {}         # widget -> (corner radius, blur radius, on_height)
        self._heights = {}

    def add_glass(self, widget, radius=18.0, blur=22.0, on_height=None):
        """Add widget over the main child, as glass.

        radius: the corner radius of the widget; it has to be the one in its CSS.
        blur: how far the blur spreads. About 22 for a small pill, about 38 for a wide bar.
        on_height: called with the widget's height whenever that changes, so that the view
        under a bar across the top can start below it.
        """
        self._glass[widget] = (float(radius), float(blur), on_height)
        self.add_overlay(widget)

    def remove_glass(self, widget):
        self._glass.pop(widget, None)
        self._heights.pop(widget, None)
        self.remove_overlay(widget)

    def do_snapshot(self, snap):
        main = self.get_child()
        node = None
        if main is not None:
            under = Gtk.Snapshot.new()
            self.snapshot_child(main, under)
            node = under.to_node()           # None when the child draws nothing
            if node is not None:
                snap.append_node(node)
        child = self.get_first_child()
        while child is not None:
            if child is not main:
                if node is not None and child in self._glass and child.get_mapped():
                    self._frost(snap, node, child)
                self.snapshot_child(child, snap)
            child = child.get_next_sibling()

    def _frost(self, snap, node, child):
        radius, blur, on_height = self._glass[child]
        ok, box = child.compute_bounds(self)     # the border box, without CSS margins
        w, h = box.get_width(), box.get_height()
        if not ok or w <= 0 or h <= 0:
            return
        if on_height and h != self._heights.get(child):
            self._heights[child] = h
            GLib.idle_add(lambda: on_height(h) and False)    # never change layout while drawing
        shape = Gsk.RoundedRect()
        shape.init_from_rect(box, min(radius, w / 2, h / 2))
        snap.push_rounded_clip(shape)
        snap.push_blur(blur)
        # Only what is near the bar is blurred: without this clip the whole view would be.
        reach = 2 * blur
        near = Graphene.Rect().init(box.get_x() - reach, box.get_y() - reach, w + 2 * reach, h + 2 * reach)
        snap.push_clip(near)
        # Past the edge of the view there is nothing, and blurring that in would fade the glass
        # out towards the edge: the view's own colour is taken to go on beyond it.
        if self.backing:
            found, color = self.get_style_context().lookup_color(self.backing)
            if found:
                snap.append_color(color, near)
        snap.append_node(node)
        snap.pop()
        snap.pop()
        snap.pop()
