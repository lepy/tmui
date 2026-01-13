#!/usr/bin/env python3
"""tmui - Interactive terminal UI for tmux session management."""
import os
import re
import shutil
import subprocess
import sys
from typing import List

__version__ = "0.1.1"

# Add vendor directory to path for bundled picotui
_vendor_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "vendor")
if _vendor_dir not in sys.path:
    sys.path.insert(0, _vendor_dir)

from picotui.context import Context
from picotui.screen import Screen
from picotui.widgets import Dialog, WListBox, WButton, WLabel, WTextEntry
from picotui.defs import KEY_ENTER
from picotui.basewidget import ACTION_OK, ACTION_CANCEL


def run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def tmux_sessions() -> List[str]:
    """
    Returns list of tmux session names. If no server is running, returns [].
    """
    cp = run(["tmux", "ls"])
    if cp.returncode != 0:
        # Typical when no tmux server exists: "failed to connect to server"
        return []
    sessions = []
    for line in cp.stdout.splitlines():
        # Example: "work: 1 windows (created Tue...)"
        m = re.match(r"^([^:]+):", line.strip())
        if m:
            sessions.append(m.group(1))
    return sessions


def exec_tmux(args: List[str]) -> None:
    """
    Replace current process with tmux command (so your terminal becomes the session).
    """
    # Restore terminal before exec
    Screen.disable_mouse()
    Screen.cursor(True)
    Screen.goto(0, 0)
    Screen.cls()
    Screen.deinit_tty()
    # Clear screen with ANSI escape after deinit
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
    os.execvp("tmux", ["tmux", *args])


def validate_session_name(name: str) -> str | None:
    """
    Validate tmux session name. Returns error message or None if valid.
    """
    if not name:
        return "Name darf nicht leer sein"
    if ":" in name:
        return "Name darf kein ':' enthalten"
    if "." in name:
        return "Name darf kein '.' enthalten"
    if name.startswith("-"):
        return "Name darf nicht mit '-' beginnen"
    if any(ord(c) < 32 for c in name):
        return "Name darf keine Steuerzeichen enthalten"
    return None


class MainDialog(Dialog):
    def __init__(self):
        # Dialog dimensions
        w, h = 72, 20
        # Center on screen
        screen_w, screen_h = Screen.screen_size()
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        super().__init__(x, y, w, h, title="tmux UI")

        self.lbl = WLabel("Session wählen (Enter=attach)  |  a=attach  n=new  r=refresh  q=quit")
        self.listbox = WListBox(50, 12, [])

        self.btn_attach = WButton(12, "Attach (a)")
        self.btn_new = WButton(10, "New (n)")
        self.btn_refresh = WButton(14, "Refresh (r)")
        self.btn_quit = WButton(10, "Quit (q)")

        self.add(1, 1, self.lbl)
        self.add(1, 3, self.listbox)

        y = 3 + self.listbox.height + 1
        self.add(1, y, self.btn_attach)
        self.add(15, y, self.btn_new)
        self.add(27, y, self.btn_refresh)
        self.add(41, y, self.btn_quit)

        self.btn_attach.on("click", self.on_attach)
        self.btn_new.on("click", self.on_new)
        self.btn_refresh.on("click", self.on_refresh)
        self.btn_quit.on("click", self.on_quit)

        self.on_refresh()

    def on_refresh(self, w=None):
        sessions = tmux_sessions()
        if not sessions:
            self.listbox.set_items(["<keine Sessions>"])
        else:
            self.listbox.set_items(sessions)
        self.listbox.cur_line = 0
        self.redraw()

    def selected_session(self) -> str | None:
        if not self.listbox.items:
            return None
        sel = self.listbox.items[self.listbox.cur_line]
        if sel.startswith("<"):
            return None
        return sel

    def on_attach(self, w=None):
        s = self.selected_session()
        if not s:
            return
        exec_tmux(["attach", "-t", s])

    def on_new(self, widget=None):
        # Simple input dialog for name
        dw, dh = 50, 8
        screen_w, screen_h = Screen.screen_size()
        dx = max(0, (screen_w - dw) // 2)
        dy = max(0, (screen_h - dh) // 2)
        dlg = Dialog(dx, dy, dw, dh, title="Neue Session")
        dlg.add(1, 1, WLabel("Name:"))
        ed = WTextEntry(30, "")
        dlg.add(7, 1, ed)
        ok = WButton(6, "OK")
        cancel = WButton(10, "Cancel")
        dlg.add(1, 3, ok)
        dlg.add(10, 3, cancel)

        ed.finish_dialog = ACTION_OK
        ok.finish_dialog = ACTION_OK
        cancel.finish_dialog = ACTION_CANCEL

        res = dlg.loop()

        if res != ACTION_OK:
            self.redraw()
            return

        name = (ed.get() or "").strip()
        err = validate_session_name(name)
        if err or not name:
            self.redraw()
            return

        # If session exists, attach instead of error.
        existing = set(tmux_sessions())
        if name in existing:
            exec_tmux(["attach", "-t", name])
        else:
            exec_tmux(["new", "-s", name])

    def on_quit(self, w=None):
        self.close()

    def handle_key(self, key):
        # key handling - keys come as bytes
        if key in (b"q", b"Q"):
            self.on_quit()
            return True
        if key in (b"r", b"R"):
            self.on_refresh()
            return True
        if key in (b"a", b"A"):
            self.on_attach()
            return True
        if key in (b"n", b"N"):
            self.on_new()
            return True
        if key == KEY_ENTER:
            self.on_attach()
            return True
        return super().handle_key(key)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-v", "--version"):
            print(f"tmui {__version__}")
            sys.exit(0)
        if sys.argv[1] in ("-h", "--help"):
            print(f"tmui {__version__} - Interactive terminal UI for tmux")
            print("\nUsage: tmui")
            print("\nShortcuts:")
            print("  a        Attach to selected session")
            print("  n        Create new session")
            print("  r        Refresh session list")
            print("  q        Quit")
            print("  Enter    Attach to selected session")
            print("  Esc      Cancel / Close dialog")
            sys.exit(0)

    if shutil.which("tmux") is None:
        print("Fehler: tmux nicht gefunden. Bitte tmux installieren.", file=sys.stderr)
        sys.exit(1)

    if os.environ.get("TMUX"):
        print("Hinweis: Du bist bereits in einer tmux-Session.", file=sys.stderr)
        print("Attach/New wird den aktuellen Client ersetzen.", file=sys.stderr)
        print("Drücke Enter um fortzufahren oder Ctrl+C zum Abbrechen...", file=sys.stderr)
        try:
            input()
        except KeyboardInterrupt:
            print()
            sys.exit(0)

    with Context():
        dlg = MainDialog()
        dlg.loop()


if __name__ == "__main__":
    main()
