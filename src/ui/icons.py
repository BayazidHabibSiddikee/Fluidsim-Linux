"""Icons package for FluidSim Linux UI."""
from PySide6.QtGui import QIcon, QPainter, QColor, QPen, QBrush, QFont, QPixmap, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF, QSize


def _icon(size=24, fn=None):
    """Create a QIcon from a drawing function."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    if fn:
        fn(p, size)
    p.end()
    return QIcon(pm)


def make_all_icons():
    """Build all UI icons eagerly. Returns dict of name -> QIcon."""
    s = 24
    icons = {}

    def I(name, fn):
        icons[name] = _icon(s, fn)

    # ---- Tool icons ----
    def draw_select(p, sz):
        pts = [QPointF(sz*0.3, sz*0.2), QPointF(sz*0.3, sz*0.85),
               QPointF(sz*0.45, sz*0.7), QPointF(sz*0.6, sz*0.9),
               QPointF(sz*0.7, sz*0.75), QPointF(sz*0.55, sz*0.65),
               QPointF(sz*0.75, sz*0.6)]
        p.setPen(QPen(QColor(60, 60, 60), 1.5))
        p.setBrush(QBrush(QColor(60, 60, 60)))
        p.drawPolygon(pts)

    def draw_wire(p, sz):
        path = QPainterPath()
        path.moveTo(sz*0.2, sz*0.8)
        path.cubicTo(sz*0.3, sz*0.5, sz*0.7, sz*0.5, sz*0.8, sz*0.8)
        p.setPen(QPen(QColor(60, 60, 60), 2))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        p.setBrush(QBrush(QColor(60, 60, 60)))
        p.drawEllipse(QPointF(sz*0.8, sz*0.8), 3, 3)

    def draw_place(p, sz):
        p.setPen(QPen(QColor(42, 130, 218), 1.5))
        p.setBrush(QBrush(QColor(42, 130, 218, 40)))
        p.drawRect(sz*0.25, sz*0.25, sz*0.5, sz*0.5)
        p.setPen(QPen(QColor(42, 130, 218), 2))
        p.drawLine(sz*0.5, sz*0.3, sz*0.5, sz*0.7)
        p.drawLine(sz*0.35, sz*0.5, sz*0.65, sz*0.5)

    def draw_delete(p, sz):
        p.setPen(QPen(QColor(200, 60, 60), 2.5))
        p.drawLine(sz*0.3, sz*0.3, sz*0.7, sz*0.7)
        p.drawLine(sz*0.7, sz*0.3, sz*0.3, sz*0.7)

    def draw_pan(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 1.5))
        p.setBrush(QBrush(QColor(60, 60, 60)))
        p.drawEllipse(QPointF(sz*0.5, sz*0.5), sz*0.35, sz*0.35)
        p.setBrush(Qt.NoBrush)
        p.drawLine(sz*0.5, sz*0.7, sz*0.5, sz*0.9)

    def draw_toggle(p, sz):
        # Directional-valve spool switch (port-switch actuation)
        p.setPen(QPen(QColor(60, 120, 60), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRect(sz*0.3, sz*0.22, sz*0.4, sz*0.5)
        # spool + stroke arrow
        p.setPen(QPen(QColor(60, 170, 60), 2))
        p.drawLine(sz*0.22, sz*0.34, sz*0.35, sz*0.5)
        p.drawLine(sz*0.35, sz*0.5, sz*0.48, sz*0.34)
        # two port stubs below
        p.setPen(QPen(QColor(60, 120, 60), 1.5))
        p.drawLine(sz*0.3, sz*0.72, sz*0.3, sz*0.9)
        p.drawLine(sz*0.7, sz*0.72, sz*0.7, sz*0.9)

    I("tool_select", draw_select)
    I("tool_wire", draw_wire)
    I("tool_place", draw_place)
    I("tool_delete", draw_delete)
    I("tool_pan", draw_pan)
    I("tool_toggle", draw_toggle)

    # ---- Toolbar action icons ----
    def draw_file_new(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRect(sz*0.2, sz*0.15, sz*0.6, sz*0.7)
        p.setPen(QPen(QColor(42, 130, 218), 2))
        p.drawLine(sz*0.5, sz*0.3, sz*0.5, sz*0.7)
        p.drawLine(sz*0.35, sz*0.5, sz*0.65, sz*0.5)

    def draw_file_open(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRect(sz*0.15, sz*0.3, sz*0.7, sz*0.55)
        p.drawLine(sz*0.15, sz*0.5, sz*0.5, sz*0.5)
        p.setBrush(QBrush(QColor(42, 130, 218)))
        p.drawEllipse(QPointF(sz*0.35, sz*0.42), 2, 2)

    def draw_file_save(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 1.5))
        p.setBrush(QBrush(QColor(42, 130, 218)))
        p.drawRect(sz*0.3, sz*0.15, sz*0.4, sz*0.15)
        p.drawRoundedRect(QRectF(sz*0.2, sz*0.3, sz*0.6, sz*0.6), 2, 2)

    def draw_undo(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 2))
        p.setBrush(Qt.NoBrush)
        path = QPainterPath()
        path.arcTo(sz*0.3, sz*0.3, sz*0.4, sz*0.4, 0, -200)
        p.drawPath(path)
        p.drawLine(sz*0.3, sz*0.5, sz*0.15, sz*0.5)
        p.drawLine(sz*0.3, sz*0.5, sz*0.3, sz*0.35)

    def draw_redo(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 2))
        p.setBrush(Qt.NoBrush)
        path = QPainterPath()
        path.arcTo(sz*0.3, sz*0.3, sz*0.4, sz*0.4, 180, 200)
        p.drawPath(path)
        p.drawLine(sz*0.7, sz*0.5, sz*0.85, sz*0.5)
        p.drawLine(sz*0.7, sz*0.5, sz*0.7, sz*0.35)

    def draw_play(p, sz):
        p.setPen(QPen(QColor(46, 204, 113), 1.5))
        p.setBrush(QBrush(QColor(46, 204, 113)))
        p.drawPolygon([QPointF(sz*0.25, sz*0.2), QPointF(sz*0.25, sz*0.8),
                       QPointF(sz*0.75, sz*0.5)])

    def draw_pause(p, sz):
        p.setPen(QPen(QColor(241, 196, 15), 1.5))
        p.setBrush(QBrush(QColor(241, 196, 15)))
        p.drawRect(sz*0.25, sz*0.2, sz*0.18, sz*0.6)
        p.drawRect(sz*0.57, sz*0.2, sz*0.18, sz*0.6)

    def draw_step(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 1.5))
        p.setBrush(QBrush(QColor(60, 60, 60)))
        p.drawRect(sz*0.15, sz*0.2, sz*0.18, sz*0.6)
        p.drawPolygon([QPointF(sz*0.4, sz*0.2), QPointF(sz*0.4, sz*0.8),
                       QPointF(sz*0.8, sz*0.5)])

    def draw_reset(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(sz/2, sz/2), sz*0.35, sz*0.35)
        p.setBrush(QBrush(QColor(60, 60, 60)))
        p.drawPolygon([QPointF(sz*0.4, sz*0.25), QPointF(sz*0.55, sz*0.5),
                       QPointF(sz*0.35, sz*0.5)])

    def draw_zoom_in(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRect(sz*0.25, sz*0.25, sz*0.35, sz*0.35)
        p.drawLine(sz*0.55, sz*0.55, sz*0.8, sz*0.8)
        p.setPen(QPen(QColor(60, 60, 60), 2))
        p.drawLine(sz*0.65, sz*0.55, sz*0.75, sz*0.55)
        p.drawLine(sz*0.7, sz*0.5, sz*0.7, sz*0.6)

    def draw_zoom_fit(p, sz):
        p.setPen(QPen(QColor(60, 60, 60), 1.5))
        p.setBrush(Qt.NoBrush)
        c = sz * 0.2
        d = sz * 0.1
        p.drawLine(c, c+d, c, c)
        p.drawLine(c, c, c+d, c)
        p.drawLine(sz-c-d, c, sz-c, c)
        p.drawLine(sz-c, c, sz-c, c+d)
        p.drawLine(c, sz-c-d, c, sz-c)
        p.drawLine(c, sz-c, c+d, sz-c)
        p.drawLine(sz-c-d, sz-c, sz-c, sz-c)
        p.drawLine(sz-c, sz-c-d, sz-c, sz-c)

    def draw_help(p, sz):
        p.setPen(QPen(QColor(42, 130, 218), 2))
        p.setBrush(QBrush(QColor(42, 130, 218)))
        p.setFont(QFont("sans-serif", 14, QFont.Bold))
        p.drawText(QRectF(0, 0, sz, sz), Qt.AlignCenter, "?")

    def draw_mode_hydro(p, sz):
        p.setPen(QPen(QColor(42, 130, 218), 1.5))
        p.setBrush(QBrush(QColor(42, 130, 218, 60)))
        p.drawEllipse(QPointF(sz*0.5, sz*0.5), sz*0.3, sz*0.3)
        p.setBrush(Qt.NoBrush)
        p.drawLine(sz*0.2, sz*0.5, sz*0.8, sz*0.5)

    def draw_mode_pneu(p, sz):
        p.setPen(QPen(QColor(100, 180, 100), 1.5))
        p.setBrush(QBrush(QColor(100, 180, 100, 60)))
        p.drawEllipse(QPointF(sz*0.5, sz*0.5), sz*0.3, sz*0.3)
        p.setBrush(Qt.NoBrush)
        p.drawLine(sz*0.2, sz*0.5, sz*0.8, sz*0.5)

    I("file_new", draw_file_new)
    I("file_open", draw_file_open)
    I("file_save", draw_file_save)
    I("edit_undo", draw_undo)
    I("edit_redo", draw_redo)
    I("sim_play", draw_play)
    I("sim_pause", draw_pause)
    I("sim_step", draw_step)
    I("sim_reset", draw_reset)
    I("zoom_in", draw_zoom_in)
    I("zoom_fit", draw_zoom_fit)
    I("help", draw_help)
    I("mode_hydraulic", draw_mode_hydro)
    I("mode_pneumatic", draw_mode_pneu)

    # Component thumbnails for library
    from src.symbols.library import draw_symbol as lib_draw
    def thumb(sym_id):
        pm = QPixmap(s, s)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(1, 1, s-2, s-2)
        try:
            lib_draw(p, sym_id, r)
        except Exception:
            p.setPen(QPen(QColor(150, 150, 150), 1))
            p.drawRect(r)
        p.end()
        return QIcon(pm)

    for key, sym in [("comp_pump", "pump"), ("comp_cylinder", "cylinder_double"),
                     ("comp_valve", "valve_4_2"), ("comp_tank", "tank"),
                     ("comp_gauge", "pressure_gauge"), ("comp_filter", "filter"),
                     ("comp_motor", "motor"), ("comp_compressor", "compressor"),
                     ("comp_battery", "battery"), ("comp_switch", "switch_toggle")]:
        icons[key] = thumb(sym)

    return icons


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
    app = QApplication(sys.argv)
    w = QWidget()
    lay = QVBoxLayout(w)
    w.setWindowTitle("Icon Preview")
    icons = make_all_icons()
    for name, icon in sorted(icons.items()):
        lbl = QLabel(f"{name}")
        lbl.setPixmap(icon.pixmap(32, 32))
        lay.addWidget(lbl)
    w.setLayout(lay)
    w.resize(200, 600)
    w.show()
    sys.exit(app.exec())
