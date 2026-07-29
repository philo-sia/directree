from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter
from PySide6.QtCore import Qt

from Directree.constants import DEFAULT_FONT_SIZE, IMAGE_PADDING, TEXT_COLOR, MAX_PAGE_HEIGHT, MAX_PREVIEW_DIMENSION, _MONOSPACE_FONTS


def _qt_color(name: str, fallback: str) -> QColor:
    color = QColor(name)
    if not color.isValid():
        color = QColor(fallback)
    return color


def _build_tree_font(font_name: str, scale: float) -> QFont:
    size = max(1, int(DEFAULT_FONT_SIZE * scale))
    font = QFont(font_name)
    font.setPixelSize(size)

    if font_name in _MONOSPACE_FONTS:
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)

    return font


def _tree_geometry(
    lines: list[str],
    scale: float,
    bottom_padding_px: int,
    font_name: str,
):
    font = _build_tree_font(font_name, scale)
    metrics = QFontMetrics(font)

    line_height = max(1, metrics.height())
    line_spacing = max(1, int(4 * scale))
    pad = max(0, int(IMAGE_PADDING * scale))
    extra_bottom = max(0, int(bottom_padding_px * scale))

    max_width = 1
    for line in lines:
        width = metrics.horizontalAdvance(line or " ")
        if width > max_width:
            max_width = width

    width = max(1, int(max_width) + 2 * pad)

    return font, metrics, line_height, line_spacing, pad, extra_bottom, width


def _page_ranges(
    line_count: int,
    line_height: int,
    line_spacing: int,
    pad: int,
    extra_bottom: int,
    max_page_height: int,
) -> list[tuple[int, int]]:
    if line_count == 0:
        return [(0, 0)]

    limit = max_page_height - 2 * pad - extra_bottom
    limit = max(line_height, limit)

    ranges: list[tuple[int, int]] = []
    start = 0
    current_height = 0
    count = 0

    for i in range(line_count):
        add = line_height + (line_spacing if count > 0 else 0)

        if count > 0 and current_height + add > limit:
            ranges.append((start, i))
            start = i
            current_height = line_height
            count = 1
        else:
            current_height += add
            count += 1

    ranges.append((start, line_count))
    return ranges


def _render_pages(
    lines: list[str],
    font: QFont,
    metrics: QFontMetrics,
    line_height: int,
    line_spacing: int,
    pad: int,
    extra_bottom: int,
    width: int,
    ranges: list[tuple[int, int]],
    bg: QColor,
    fg: QColor,
) -> list[QImage]:
    pages: list[QImage] = []

    for index, (s, e) in enumerate(ranges):
        n = e - s
        height = max(
            1,
            n * line_height
            + max(0, n - 1) * line_spacing
            + 2 * pad
            + (extra_bottom if index == len(ranges) - 1 else 0),
        )

        img = QImage(width, height, QImage.Format.Format_RGB32)
        img.fill(bg)

        painter = QPainter(img)
        painter.setFont(font)
        painter.setPen(fg)

        y = pad + metrics.ascent()
        for i in range(s, e):
            painter.drawText(pad, y, lines[i] or "")
            y += line_height + line_spacing

        painter.end()
        pages.append(img)

    return pages


def render_tree_qimages(
    text: str,
    scale: float,
    bottom_padding_px: int,
    font_name: str,
    bg_color: str,
    text_color: str = TEXT_COLOR,
    max_page_height: int = MAX_PAGE_HEIGHT,
) -> list[QImage]:
    lines = text.splitlines() or [""]

    font, metrics, line_height, line_spacing, pad, extra_bottom, width = _tree_geometry(
        lines, scale, bottom_padding_px, font_name
    )

    if width > max_page_height:
        scale *= max_page_height / width
        font, metrics, line_height, line_spacing, pad, extra_bottom, width = _tree_geometry(
            lines, scale, bottom_padding_px, font_name
        )

    ranges = _page_ranges(len(lines), line_height, line_spacing, pad, extra_bottom, max_page_height)

    bg = _qt_color(bg_color, "white")
    fg = _qt_color(text_color, "black")

    return _render_pages(
        lines, font, metrics, line_height, line_spacing, pad, extra_bottom, width, ranges, bg, fg
    )


def render_tree_qimage_full(
    text: str,
    scale: float,
    bottom_padding_px: int,
    font_name: str,
    bg_color: str,
    text_color: str = TEXT_COLOR,
    max_height: int = MAX_PAGE_HEIGHT,
) -> QImage:
    lines = text.splitlines() or [""]

    font, metrics, line_height, line_spacing, pad, extra_bottom, width = _tree_geometry(
        lines, scale, bottom_padding_px, font_name
    )

    n = len(lines)
    native_height = max(1, n * line_height + max(0, n - 1) * line_spacing + 2 * pad + extra_bottom)

    if native_height > max_height:
        reduced_scale = scale * (max_height / native_height)
        font, metrics, line_height, line_spacing, pad, extra_bottom, width = _tree_geometry(
            lines, reduced_scale, bottom_padding_px, font_name
        )

    bg = _qt_color(bg_color, "white")
    fg = _qt_color(text_color, "black")

    return _render_pages(
        lines, font, metrics, line_height, line_spacing, pad, extra_bottom, width,
        [(0, len(lines))], bg, fg,
    )[0]
