[English](README.md) · [简体中文](README.zh-CN.md) · **繁體中文** · [日本語](README.ja.md)

# GTK 4 的磨砂玻璃

讓浮在檢視上方的列透出它下面模糊的內容，用於以 GTK 4 撰寫的 GNOME 應用程式。只有一個很小的
Python 檔案 [`glass.py`](glass.py)，除了 GTK 4 之外沒有任何相依套件。

![頂端的一條列和一個小膠囊形工具列，都是磨砂玻璃，下面是彩色方塊的格狀排列](screenshot.png)

它來自 [Inkpad](https://github.com/LoveProgramming-cc/Inkpad-gnome)，那裡頁面上方和文件庫
上方的列就是這樣畫的。

## 試試看

需要 Python 3、PyGObject、GTK 4 和 libadwaita（示範程式用到 libadwaita，`glass.py` 本身
不用）。在 Ubuntu 或 Debian 上：

```sh
sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1
python3 demo.py
```

把格狀內容捲動到頂端的列下面看看。

## 使用方式

把 `glass.py` 複製到你的應用程式裡。`GlassOverlay` 就是一個 `Gtk.Overlay`；加入列時用
`add_glass` 取代 `add_overlay`：

```python
from glass import GlassOverlay

overlay = GlassOverlay(child=scrolled_view, backing='view_bg_color')
overlay.add_glass(pill, radius=18, blur=22)
```

```css
.pill {
  background: alpha(@popover_bg_color, 0.72);   /* 蓋在模糊之上的一層顏色 */
  border-radius: 18px;                          /* 與 add_glass 裡的半徑相同 */
}
```

| 參數 | 意義 |
|---|---|
| `radius` | 列的圓角半徑，必須與它 CSS 裡的一致。 |
| `blur` | 模糊擴散的範圍：小膠囊約 22，寬的列約 38。 |
| `on_height` | 列的高度改變時被呼叫，參數是高度；見下面的問題 4。 |
| `backing`（在 overlay 上） | 玻璃下面的檢視所填滿的主題顏色；見問題 2。 |

## 你需要它嗎？GTK 4.22 已有 `backdrop-filter`

**如果你的應用程式可以要求 GTK 4.22 或更新版本，就不需要 `glass.py`。** 從 GTK 4.22
（2026 年 3 月；最早出現在開發版 4.21.2）起，GTK 的 CSS 支援 `backdrop-filter`，一行就能
做到同樣的事：

```css
.pill {
  background: alpha(@popover_bg_color, 0.72);
  backdrop-filter: blur(11px);
  border-radius: 18px;
}
```

`python3 demo.py --native` 用這種方式執行示範程式，用的是一般的 `Gtk.Overlay`；在 GTK 4.22
上兩者看起來一樣。（GTK 4.22 和 libadwaita 1.9 裡沒有叫 `BlurOverlay` 的元件；內建的方法
就是這個 CSS 屬性。）

`GlassOverlay` 是給還要在舊版 GTK 4 上執行的應用程式用的，舊版不認得這個屬性：Ubuntu 24.04
是 GTK 4.14，Debian 13 是 4.18，GNOME 49 是 4.20。

| | CSS `backdrop-filter` | `GlassOverlay`（本儲存庫） |
|---|---|---|
| 需要 | GTK 4.22 或更新 | GTK 4；在 4.6 到 4.22 上測試過，見[測試過的版本](#測試過的版本) |
| 程式碼 | 一行 CSS | 約 90 行的 Python 類別，複製到應用程式裡 |
| 適用範圍 | 任何元件 | 只有用 `add_glass` 加進 overlay 的元件 |
| 模糊的內容 | 元件背後畫出的一切 | 只有 overlay 的主要子元件，不包括其他列 |
| 圓角半徑 | 跟隨 `border-radius` | 寫兩次：CSS 裡和 `add_glass` 裡 |
| 玻璃下的檢視要不透明（問題 1） | 在示範程式裡不需要 | 需要 |
| 邊緣之外的顏色（問題 2） | 不需要 | `backing=` |
| 讓內容進到頂端列下面（問題 4） | 仍要自己安排 | 仍要自己安排；`on_height=` 可以幫忙 |
| 模糊的數值 | `blur(N px)`：N 是標準差 | `blur=R`：擴散範圍相當於 CSS 的 `blur(R/2)` |
| 其他語言 | 任何語言（它只是 CSS） | Python；同樣的呼叫在 C、Rust、Vala 和 JavaScript 裡都有 |

關於數值：在 GTK 4.22 上測得，CSS 的 `blur(20px)` 把一條清晰的邊界變成 48 px 的過渡，這裡
的 `blur=22` 則是 26 px。所以 CSS 的 `blur(11px)` 相當於 `blur=22`，`blur(19px)` 相當於
`blur=38`。

應用程式也可以在執行時選擇：`Gtk.get_minor_version() >= 22` 時用 CSS，否則用 `GlassOverlay`。

## 它是什麼，不是什麼

人們說的「磨砂玻璃」有兩種：

| | 模糊的是 | 由誰繪製 | 可用於 |
|---|---|---|---|
| **應用程式內的玻璃**（本儲存庫） | 列下面應用程式自己的內容 | 應用程式自己，用 GTK | GNOME、KDE，任何桌面 |
| **視窗玻璃** | 應用程式背後的桌面和其他視窗 | 合成器 | 只有具備模糊協定的合成器（KWin）；GNOME Shell 不行 |

在 GTK 4.22 之前，GTK 的 CSS 沒有 `backdrop-filter`，所以只用半透明背景得到的是一條透明
的列，而不是磨砂的列。模糊必須自己畫。GTK 的場景圖（GSK）有模糊節點，有它就夠了。

## 原理

浮在檢視上方的列是 `Gtk.Overlay` 的子元件。Overlay 先畫主要子元件，再把每條列畫在上面。
要讓一條列變成磨砂的，overlay 在畫這條列之前，把主要子元件再畫一遍——模糊過，並裁切成列的
形狀：

1. 把主要子元件記錄成一個繪製節點，只記錄一次。
2. 畫出這個節點。
3. 對每條列：裁切到列的圓角矩形，推入模糊，再畫一次同一個節點。
4. 畫列本身。它的 CSS 背景是半透明的，於是替模糊染上顏色。

節點只記錄一次並重複使用，所以檢視不會被排版或點陣化兩次；GPU 只需模糊每條列下面的一小塊
區域。核心程式碼：

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

## 四個會出問題的地方

這些都是在寫 Inkpad 的版本時遇到的。`glass.py` 和 `demo.py` 已經逐一處理。問題 1 到 3
屬於 `GlassOverlay`；問題 4 用 CSS 的 `backdrop-filter` 時同樣存在。

### 1. 被模糊的那一層有洞，看起來像一塊平平的灰色

如果列下面的檢視背景是透明的（它的顏色由父元件來畫），記錄下來的節點裡就只有各個項目，
項目之間什麼都沒有。模糊之後是一片半透明的暈染，下面清晰的畫面會透出來。模糊越強越糟：
看起來有條紋，或者顯出畫面的殘影。

**解決方法：** 讓被模糊的檢視不透明。給 overlay 的主要子元件一個自己的背景：

```css
.under { background: @view_bg_color; }
```

### 2. 玻璃在檢視邊緣附近逐漸消失

檢視邊緣之外什麼都沒有，模糊會把這個「什麼都沒有」混進來。緊貼視窗頂端的列，越靠近上邊緣
就越暗（或越亮）。

**解決方法：** 傳入 `backing='view_bg_color'` 給 `GlassOverlay`。它會在模糊內部、畫檢視
之前，先用這個顏色塗滿一塊比列更大的區域，於是檢視看起來延伸到了邊緣之外。

### 3. 模糊的範圍超過了列能顯示的範圍

如果模糊內部不加裁切，每條列都會讓 GTK 去模糊整個檢視。`glass.py` 把檢視裁切到列的範圍
向外擴大兩倍模糊半徑。

關於強度：直接把半徑調大就行。在 GTK 4.22（Vulkan 繪製器）上測得，一條黑白邊界被模糊後，
10–90 % 的過渡寬度與半徑同步增加：

| 半徑 | 邊界寬度 |
|---|---|
| 10 | 12 px |
| 22 | 26 px |
| 44 | 52 px |
| 88 | 104 px |

### 4. 內容必須能捲到列的下面

下面什麼都沒有的玻璃，看起來就是一條普通的列。在垂直的方框裡，放在捲動清單*上方*的標題列
背後永遠沒有東西。要把標題列放進 overlay，讓清單從它下面捲過；再給清單一個等於列高度的
上邊界，讓第一列項目從列的下方開始：

```python
overlay.add_glass(bar, radius=0, blur=38,
                  on_height=lambda h: flow.set_margin_top(int(h) + 10))
```

高度是在 overlay 的 snapshot 裡回報的，那時列的範圍已經知道；回呼在閒置處理函式裡執行，
因為繪製過程中不能改變排版。（在 Inkpad 裡，用 Python 覆寫 `Gtk.Box` 子類別的
`do_size_allocate` 並沒有被呼叫，所以才這樣做。）

## 數值的選擇

| | 浮動的小膠囊 | 捲動清單上方的寬列 |
|---|---|---|
| 模糊半徑 | 22 | 38 |
| 染色 | 彈出層顏色，72 % | 檢視顏色，74 % |
| 效果 | 內容柔化，但仍能辨認 | 內容變成柔和的色塊 |

## 測試過的版本

`python3 test.py` 畫出一個視窗：一條清晰的黑白邊界，上面有一條玻璃列和一個玻璃膠囊，然後
測量——玻璃下面的邊界必須是模糊的，旁邊必須是清晰的。它只用 GTK，不用 libadwaita。在下列
版本上通過：

| GTK | 來自 | 繪製器 | 結果 |
|---|---|---|---|
| 4.6.9 | Ubuntu 22.04 | GL | 通過 |
| 4.8.3 | Debian 12 | GL | 通過 |
| 4.14.5 | Ubuntu 24.04 | NGL | 通過 |
| 4.18.5 | Ubuntu 套件庫 | GL | 通過 |
| 4.20.1 | Ubuntu 套件庫 | Vulkan | 通過 |
| 4.22.4 | Ubuntu 26.04 | Vulkan | 通過 |

每個版本在 `blur=22` 時都得到同樣的 26 px 邊界。除 4.22 外，這些版本都不接受 CSS 裡的
`backdrop-filter`（「No property named」），所以在它們上面要得到磨砂玻璃，就得用
`GlassOverlay`。

測試方式：從各發行版的套件裡取出對應版本的 GTK 函式庫，在同一台機器（Ubuntu 26.04，Wayland）
上載入，用的是這台機器自己的 GLib、Pango、PyGObject 和顯示卡驅動程式。沒有在那些舊發行版
本身上執行，也沒有在 X11 上、或在比 4.6 更舊的 GTK 上執行。`demo.py` 需要 libadwaita 和
`load_from_string`（GTK 4.12），只在 4.22 上執行過。

## 限制

- **彈出層和選單仍然不透明。** 它們是獨立的表面，overlay 畫不到它們背後的內容。
- **圓角半徑要寫兩次，** CSS 裡一次，`add_glass` 裡一次。GTK 不把元件計算後的圓角半徑
  交給 Python。
- **每條玻璃列都是一次額外的模糊，** 它下面的檢視每重繪一次就做一次。在 GPU 繪製器
  （GL、Vulkan）上負擔很小；用 Cairo 軟體繪製器（`GSK_RENDERER=cairo`）時模糊很慢。
- **`lookup_color` 在 GTK 4 中已被棄用。** 目前仍可用；替代方法是從你自己的調色盤把顏色
  傳進來。
- **視窗玻璃**（視窗背後的桌面被模糊）是另一回事，GNOME 上的 GTK 應用程式做不到。

## 不用截圖工具來檢查

可以在應用程式內部把視窗畫成 PNG，在截圖需要授權的 Wayland 上也能用。
`python3 demo.py --png out.png` 做的就是這件事：

```python
snap = Gtk.Snapshot.new()
Gtk.WidgetPaintable.new(window).snapshot(snap, window.get_width(), window.get_height())
texture = window.get_renderer().render_texture(snap.to_node(), None)
texture.save_to_png('window.png')
```

先把一些內容捲到列下面：背後沒有東西的玻璃是無法判斷效果的。

## 授權

著作權所有 © 2026 Inkpad 作者。

以 [MIT 授權條款](LICENSE)釋出：可以用在任何專案裡，無論自由軟體還是專有軟體，只要保留著作權
和授權聲明。

這些程式碼來自 [Inkpad](https://github.com/LoveProgramming-cc/Inkpad-gnome)。Inkpad 整體採用
GNU GPL 第 3 版或更新版本；它的授權為磨砂玻璃部分（`inkpad/glass.py`）設了例外：作者同時
以 MIT 授權條款在這裡提供這一部分。
