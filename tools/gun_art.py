"""The revolver on the updater: Jack's gun, with a suppressor on it.

Jack Burton's gun in Big Trouble in Little China is a Smith & Wesson Model 29 -
Egg Shen hands it to him before the final fight with Lo Pan. (The Chang Sing carry
Beretta 92SBs, which is the pistol people tend to remember.) This is that
revolver as it reads on the updater: a six-shot cylinder carrying fat .44 rounds,
a bolt-on suppressor at the muzzle, and the progress bar leaving the end of it.

Two things are load bearing. The barrel line ends |]= so the bar has a muzzle to
leave from, and that line is the longest in the block, so the column the count is
written at can be measured from it. tools/check_launchers.py checks both against
whatever ends up in the file.

    python3 tools/gun_art.py            print the drawing
    python3 tools/gun_art.py --write    put it in "Update and Play.bat"
"""
import io
import re
import sys

LAUNCHER = "Update and Play.bat"

# The drawing, without the commands: four spaces in, muzzle to the right. The bar
# starts at the |]= on the barrel line and runs to the right of it.
ART = [
    "..._...|..____________________, ,",
    "....../ '---___________----_____|##########|]=",
    "...../_=(O)(O)(O);;;_______.:/|##########|",
    ".....), ---.(_(__) /\\",
    '....// (..) ), ----"',
    "...//___//",
    "..//___//",
    ".//___//",
]


def escape(text):
    for ch in "|<>()&":
        text = text.replace(ch, "^" + ch)
    return text


def write():
    """Puts the drawing where the launcher draws it.

    Found by shape rather than by matching the old characters: the block to
    replace is whatever sits between the game's title and the line that follows
    it, in both labels that draw the pistol. That way an edit to the drawing
    here cannot leave the launcher holding a picture this tool no longer knows.
    """
    raw = io.open(LAUNCHER, "rb").read().decode("utf-8")
    text = raw.replace("\r\n", "\n")
    lines = text.split("\n")
    muzzle_row = max(range(len(ART)), key=lambda i: len(ART[i]))
    rows = ["echo    " + escape(r) for r in ART]
    drawn = list(rows)
    drawn[muzzle_row] = drawn[muzzle_row] + "  %RBAR% %RPCT%"

    def replace_art(label, stop):
        start = next(k for k, l in enumerate(lines) if l.strip() == label)
        title = start
        while not lines[title].startswith("echo    BIG TROUBLE"):
            title += 1
            if title > start + 40:
                raise SystemExit("%s has no title above its drawing" % label)
        end = title + 1
        while end < len(lines) and not stop(lines[end]):
            end += 1
        if not any("echo" in l for l in lines[title + 1:end]):
            raise SystemExit("%s has no drawing under its title" % label)
        lines[title + 1:end] = rows if label == ":gun" else drawn

    replace_art(":gun", lambda l: l.startswith('set "GUNSHOWN=1"'))
    replace_art(":gunredraw", lambda l: not l.startswith("echo    "))
    text = "\n".join(lines)
    muzzle = len("    " + ART[muzzle_row]) + 3
    text, n = re.subn(r'set "MUZZLE=\d+"', 'set "MUZZLE=%d"' % muzzle, text, count=1)
    if n != 1:
        raise SystemExit("MUZZLE is not set where this tool expects it")
    io.open(LAUNCHER, "wb").write(text.replace("\n", "\r\n").encode("utf-8"))
    return muzzle


def main():
    width = max(len(r) for r in ART) + 4
    print("    " + "".join(str(i // 10 % 10) for i in range(width)))
    print("    " + "".join(str(i % 10) for i in range(width)))
    for r in ART:
        print("    " + r)
    muzzle = max(len(r) for r in ART) + 4 + 3
    print("\n%d rows, MUZZLE %d" % (len(ART), muzzle))
    if "--write" in sys.argv:
        print("wrote MUZZLE %d into %s" % (write(), LAUNCHER))


if __name__ == "__main__":
    main()
