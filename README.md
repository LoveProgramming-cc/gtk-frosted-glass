**English** · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md)

# Frosted glass for GTK 4

Bars that float over a view and show it blurred through them, for GNOME apps written with
GTK 4. One small Python file, [`glass.py`](glass.py), with no dependency beyond GTK 4.

![A bar across the top and a small pill, both frosted, over a grid of coloured tiles](screenshot.png)

It comes from [Inkpad](https://github.com/LoveProgramming-cc/Inkpad-gnome), where the bars
over the page and over the library are drawn this way.

## Try it

Needs Python 3, PyGObject, GTK 4 and libadwaita (the demo uses libadwaita; `glass.py` does
not). On Ubuntu or Debian:

```sh
sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1
python3 demo.py
```

Scroll the grid under the bar at the top.

## Use it

Copy `glass.py` into your app. `GlassOverlay` is a `Gtk.Overlay`; add a bar with `add_glass`
instead of `add_overlay`:

```python
from glass import GlassOverlay

overlay = GlassOverlay(child=scrolled_view, backing='view_bg_color')
overlay.add_glass(pill, radius=18, blur=22)
```

```css
.pill {
  background: alpha(@popover_bg_color, 0.72);   /* the wash over the blur */
  border-radius: 18px;                          /* the same radius as in add_glass */
}
```

| Argument | Meaning |
|---|---|
| `radius` | The bar's corner radius. It has to be the one in its CSS. |
| `blur` | How far the blur spreads: about 22 for a small pill, about 38 for a wide bar. |
| `on_height` | Called with the bar's height when it changes; see problem 4 below. |
| `backing` (on the overlay) | The theme colour the view under the glass is filled with; see problem 2. |

## What it is, and what it is not

There are two things people call frosted glass:

| | Blurs | Who draws it | Works on |
|---|---|---|---|
| **In-app glass** (this repository) | the app's own content under a bar | the app, with GTK | GNOME, KDE, any desktop |
| **Window glass** | the desktop and other windows behind the app | the compositor | only compositors with a blur protocol (KWin); not GNOME Shell |

GTK's CSS has no `backdrop-filter`, so a translucent background alone only gives a
see-through bar, not a frosted one. The blur has to be drawn by hand. GTK's scene graph (GSK)
has a blur node, and that is all that is needed.

## How it works

A bar that floats over a view is a child of a `Gtk.Overlay`. The overlay draws its main child,
then each bar on top. To frost a bar, the overlay draws the main child a second time, blurred
and clipped to the bar's shape, just before it draws the bar:

1. Record the main child once as a render node.
2. Draw that node.
3. For each bar: clip to the bar's rounded rectangle, push a blur, draw the same node again.
4. Draw the bar itself. Its CSS background is translucent, so it tints the blur.

The node is recorded once and reused, so the view is not laid out or rasterised twice; the
GPU only blurs the small area under each bar. The core of it:

```python
def do_snapshot(self, snap):
    main = self.get_child()
    under = Gtk.Snapshot.new()
    self.snapshot_child(main, under)
    node = under.to_node()
    snap.append_node(node)
    for bar in bars:
        snap.push_rounded_clip(shape_of(bar))
        snap.push_blur(22.0)
        snap.append_node(node)
        snap.pop()
        snap.pop()
        self.snapshot_child(bar, snap)
```

## Four things that go wrong

These all happened while writing Inkpad's version. `glass.py` and `demo.py` handle each.

### 1. The blurred layer has holes, so it looks like a flat grey box

If the view under the bar has a transparent background (its colour is painted by a parent),
the recorded node contains only the items, with nothing between them. Blurred, that is a
half-transparent smear, and the sharp picture underneath shows through it. A stronger blur
makes it worse: it looks streaked, or shows a ghost of the picture.

**Fix:** make the blurred view opaque. Give the overlay's main child its own background:

```css
.under { background: @view_bg_color; }
```

### 2. The glass fades out near the edge of the view

Beyond the edge of the view there is nothing, and the blur mixes that nothing in. A bar at the
very top of a window turns dark (or light) towards its top edge.

**Fix:** pass `backing='view_bg_color'` to `GlassOverlay`. Inside the blur it paints that
colour over an area larger than the bar before drawing the view, so the view appears to
continue past its edge.

### 3. Blurring more than the bar can show

Without a clip inside the blur, GTK is asked to blur the whole view for every bar. `glass.py`
clips the view to the bar's bounds grown by twice the blur radius.

On strength: the radius can simply be raised. Measured on GTK 4.22 (Vulkan renderer), the
10–90 % width of a blurred black/white edge grows in step with it:

| Radius | Edge width |
|---|---|
| 10 | 12 px |
| 22 | 26 px |
| 44 | 52 px |
| 88 | 104 px |

### 4. Content has to be able to go under the bar

Glass over nothing looks like a plain bar. A header that sits *above* a scrolled list in a
vertical box never has anything behind it. Put the header in the overlay, so the list scrolls
underneath, and give the list a top margin equal to the bar's height so that its first row
starts below the bar:

```python
overlay.add_glass(bar, radius=0, blur=38,
                  on_height=lambda h: flow.set_margin_top(int(h) + 10))
```

The height is reported from the overlay's snapshot, where the bar's bounds are already known,
and the callback runs from an idle handler, because layout must not change while drawing.
(Overriding `do_size_allocate` on a `Gtk.Box` subclass in Python was not called in Inkpad,
which is why it is done this way.)

## Choosing the numbers

| | Small floating pill | Wide bar over a scrolling list |
|---|---|---|
| Blur radius | 22 | 38 |
| Tint | popover colour at 72 % | view colour at 74 % |
| Result | content stays recognisable, softened | content becomes soft patches of colour |

## Limits

- **Popovers and menus stay opaque.** They are separate surfaces, so the overlay cannot
  draw what is behind them.
- **The corner radius is written twice,** in the CSS and in `add_glass`. GTK does not give a
  widget's computed border radius to Python.
- **Each glass bar is an extra blur** every time the view under it redraws. It is cheap on
  the GPU renderers (GL, Vulkan). With the Cairo software renderer (`GSK_RENDERER=cairo`)
  blur is slow.
- **`lookup_color` is deprecated** in GTK 4. It still works; the alternative is to pass the
  colour in from your own palette.
- **Window glass** (the desktop blurred behind the window) is a different thing and is not
  available to GTK apps on GNOME.
- Tested on GTK 4.22 and libadwaita 1.9 only.

## Checking it without a screenshot tool

A window can be drawn to a PNG from inside the app, which also works on Wayland where
screenshots need permission. `python3 demo.py --png out.png` does this:

```python
snap = Gtk.Snapshot.new()
Gtk.WidgetPaintable.new(window).snapshot(snap, window.get_width(), window.get_height())
texture = window.get_renderer().render_texture(snap.to_node(), None)
texture.save_to_png('window.png')
```

Scroll some content under the bar first: glass with nothing behind it cannot be judged.

## Licence

Copyright © 2026 the Inkpad authors.

Free software under the [GNU General Public License, version 3](LICENSE) or (at your option)
any later version, the same licence as Inkpad, which this code comes from.
