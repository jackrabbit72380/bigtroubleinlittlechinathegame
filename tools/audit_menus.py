"""Audit every screen's menu text against the main menu.

The main menu is the reference: its item face, its on-screen text height, its row
pitch and its centre. Every other menu is measured the same way - face, ink height,
draw scale, pitch, anchor x - so a screen that sets its text at another size, or
spaces its rows out unevenly, or sits off the centre, shows up as a line of numbers
instead of a matter of opinion.

Run:  python3 tools/audit_menus.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF = os.path.join(ROOT, "data", "ikemen1", "system.def")
FONTS = os.path.join(ROOT, "data", "ikemen1", "fonts")
BASE = os.path.join(ROOT, "data", "system.base.def")

TEXT_KEYS = re.compile(
    r"(menu\.item|menu\.item\.active|menu\.item\.selected|menu\.item\.selected\.active"
    r"|menu\.item\.value|menu\.item\.value\.active|menu\.item\.value\.conflict"
    r"|menu\.item\.info|menu\.item\.info\.active|title|keymenu\.item|keymenu\.item\.active"
    r"|keymenu\.item\.selected|keymenu\.item\.selected\.active|movelist\.text|movelist\.title"
    r"|stage|stage\.active|stage\.active2|stage\.done|loading|wintext|winquote|continue"
    r"|p1\.name|p2\.name|item\.rank|item\.name|item\.result|credits)\.font$", re.I)


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        head = re.match(r"^\s*\[([^\]]+)\]", line)
        if head:
            cur = head.group(1).strip().lower()
            out.setdefault(cur, {})
            continue
        if cur is None:
            continue
        body = line.split(";", 1)[0]
        kv = re.match(r"^\s*([A-Za-z0-9_.]+)\s*=\s*(.*)$", body)
        if kv:
            out[cur][kv.group(1).lower()] = kv.group(2).strip()
    return out


def font_table(text):
    """fontN -> (file name, ink height), from the motif and the baked faces."""
    files = {}
    for line in text.splitlines():
        hit = re.match(r"^\s*font(\d+)\s*=\s*(\S+)", line, re.I)
        if hit:
            files[int(hit.group(1))] = hit.group(2)
    table = {}
    for number, name in files.items():
        path = os.path.join(ROOT, "data", name)
        if not os.path.exists(path):
            path = os.path.join(os.path.dirname(DEF), name)
        size = None
        text_def = read(path)
        hit = re.search(r"^\s*Size\s*=\s*(-?\d+)\s*,\s*(-?\d+)", text_def, re.M | re.I)
        if hit:
            size = (int(hit.group(1)), int(hit.group(2)))
        table[number] = (os.path.basename(name), size)
    return table


def spec(value, fonts):
    """'10,0,0, 240,196,88' -> (face, ink height, align)."""
    parts = [p.strip() for p in value.split(",")]
    try:
        number = int(parts[0])
    except (ValueError, IndexError):
        return None
    face, size = fonts.get(number, ("font%d" % number, None))
    align = parts[2] if len(parts) > 2 else "?"
    ink = size[1] if size and size[1] > 0 else (size[0] if size and size[0] > 0 else None)
    return face, ink, align


def scale_of(sec, key):
    """The draw scale a text key uses: its own, else the item family's, else 1."""
    base = key[:-5] if key.lower().endswith(".font") else key
    for name in (base + ".scale", base.rsplit(".", 1)[0] + ".scale", "menu.item.scale"):
        value = sec.get(name)
        if value:
            nums = [float(v) for v in value.split(",")]
            return nums[1] if len(nums) > 1 else nums[0]
    return 1.0


def main():
    text = read(DEF)
    fonts = font_table(text)
    secs = sections(text)
    print("faces:")
    for number in sorted(fonts):
        print("  font%-3d %-18s ink=%s" % (number, fonts[number][0], fonts[number][1]))

    ref = secs.get("title info", {})
    ref_spec = spec(ref.get("menu.item.font", ""), fonts)
    ref_scale = scale_of(ref, "menu.item.font")
    ref_ink = ref_spec[1] * ref_scale if ref_spec and ref_spec[1] else None
    ref_pitch = float(ref.get("menu.item.spacing", "0, 40").split(",")[1])
    ref_x = float(ref.get("menu.pos", "0, 0").split(",")[0])
    print("\nmain menu: face %s ink %s x%.2f -> %.0fpx tall, pitch %.0f, anchor x %.0f"
          % (ref_spec[0] if ref_spec else "?", ref_spec[1] if ref_spec else "?",
             ref_scale, ref_ink or 0, ref_pitch, ref_x))

    problems = []
    for name in sorted(secs):
        sec = secs[name]
        keys = [k for k in sec if TEXT_KEYS.match(k)]
        if not keys:
            continue
        pos = sec.get("menu.pos", "")
        spacing = sec.get("menu.item.spacing", "")
        visible = sec.get("menu.window.visibleitems", "")
        print("\n[%s]  pos=%s spacing=%s visible=%s" % (name, pos or "-", spacing or "-", visible or "-"))
        for key in sorted(keys):
            got = spec(sec[key], fonts)
            if got is None:
                continue
            face, ink, align = got
            scl = scale_of(sec, key)
            shown = (ink * scl) if ink else None
            mark = ""
            if shown is not None and ref_ink:
                if abs(shown - ref_ink) > 1.5:
                    mark = "  <-- %+.0fpx vs main menu" % (shown - ref_ink)
                    problems.append("%s %s draws at %.0fpx, the main menu at %.0fpx"
                                    % (name, key, shown, ref_ink))
            print("    %-34s %-16s ink=%-4s x%.2f -> %-6s align=%s%s"
                  % (key, face, ink, scl, "%.0f" % shown if shown else "auto", align, mark))
        pitch = None
        if spacing:
            pitch = float(spacing.split(",")[1])
            # the main menu's pitch is the reference, the way its text size is:
            # a tighter one squeezes the rows together, a wider one spreads the
            # list out, and either reads as a screen that is not the same screen
            if abs(pitch - ref_pitch) > 2:
                problems.append("%s rows are %.0fpx apart, the main menu's are %.0f"
                                % (name, pitch, ref_pitch))
            if ref_ink and pitch + 8 < ref_ink:
                problems.append("%s rows are %.0fpx apart for %.0fpx text"
                                % (name, pitch, ref_ink))
        if pos:
            x = float(pos.split(",")[0])
            if abs(x - 960) > 200 and name != "title info":
                problems.append("%s anchors at x %.0f, not the frame's middle" % (name, x))
        if pitch and visible:
            try:
                last = float(pos.split(",")[1]) + (int(float(visible)) - 1) * pitch
            except (ValueError, IndexError):
                continue
            if last > 1040:
                problems.append("%s row %s ends at y %.0f" % (name, visible, last))

    print("\n=== findings: %d ===" % len(problems))
    for line in problems:
        print("  %s" % line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
