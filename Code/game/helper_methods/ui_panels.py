"""In-main-window panel helpers and coalesced messagebox reporting."""

import tkinter as tk
from tkinter import messagebox


class ModalPanel:
    """Full-size overlay Frame that replaces a Toplevel popup."""

    def __init__(self, parent, title=None):
        self.parent = parent
        self.frame = tk.Frame(parent, bg="black")
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.frame.lift()
        self._closed = False
        self._tk_destroy = self.frame.destroy
        if title:
            try:
                self._prev_title = parent.winfo_toplevel().title()
                parent.winfo_toplevel().title(title)
            except tk.TclError:
                self._prev_title = None
        else:
            self._prev_title = None

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self._prev_title is not None:
            try:
                self.parent.winfo_toplevel().title(self._prev_title)
            except tk.TclError:
                pass
        try:
            self._tk_destroy()
        except tk.TclError:
            pass

    # Compatibility with code that called popup.destroy()
    def destroy(self):
        self.close()

    def configure(self, **kwargs):
        return self.frame.configure(**kwargs)

    def config(self, **kwargs):
        return self.frame.config(**kwargs)

    def pack(self, *args, **kwargs):
        return self.frame.pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        return self.frame.grid(*args, **kwargs)

    def place(self, *args, **kwargs):
        return self.frame.place(*args, **kwargs)

    def bind(self, *args, **kwargs):
        return self.frame.bind(*args, **kwargs)

    def unbind(self, *args, **kwargs):
        return self.frame.unbind(*args, **kwargs)

    def after(self, *args, **kwargs):
        return self.frame.after(*args, **kwargs)

    def focus_force(self):
        return self.frame.focus_force()

    def focus_get(self):
        return self.frame.focus_get()

    def update_idletasks(self):
        return self.frame.update_idletasks()

    def winfo_children(self):
        return self.frame.winfo_children()

    def winfo_toplevel(self):
        return self.frame.winfo_toplevel()

    def winfo_exists(self):
        try:
            return self.frame.winfo_exists()
        except tk.TclError:
            return False

    def cget(self, key):
        return self.frame.cget(key)


def open_modal_panel(parent, title=None, geometry=None):
    """
    Place a full-size black Frame over parent.
    Returns (panel, content_frame) where content_frame is where widgets should be packed.
    panel.destroy() / panel.close() removes only the overlay.
    content_frame.destroy() is redirected to panel.close() for drop-in Toplevel replacement.
    geometry is accepted for API compatibility but ignored (overlay fills parent).
    """
    del geometry  # overlays fill the parent; size is not applied to a separate window
    panel = ModalPanel(parent, title=title)
    # Allow existing popup.destroy() call sites to close the overlay cleanly
    panel.frame.destroy = panel.close
    return panel, panel.frame


def open_sub_screen(parent, title, on_close):
    """
    Clear parent and prepare it for a full-screen in-window UI.
    Same pattern as open_room_in_main_window; caller restores previous UI in on_close.
    """
    for widget in parent.winfo_children():
        widget.destroy()
    parent.title(title)
    parent.configure(bg="black")
    parent.protocol("WM_DELETE_WINDOW", on_close)
    return parent


_KIND_RANK = {"info": 0, "warning": 1, "error": 2}
_KIND_FN = {
    "info": messagebox.showinfo,
    "warning": messagebox.showwarning,
    "error": messagebox.showerror,
}


class MessageBuffer:
    """Debounce rapid messagebox calls into a single dialog."""

    def __init__(self, parent, delay_ms=80):
        self.parent = parent
        self.delay_ms = delay_ms
        self._pending = []
        self._after_id = None

    def report(self, title, message, kind="info"):
        """Queue a message; flush as one dialog after a short debounce."""
        self._pending.append((title, message, kind))
        if self._after_id is not None:
            try:
                self.parent.after_cancel(self._after_id)
            except (tk.TclError, ValueError):
                pass
        self._after_id = self.parent.after(self.delay_ms, self._flush)

    def flush_now(self):
        """Immediately show any pending messages."""
        if self._after_id is not None:
            try:
                self.parent.after_cancel(self._after_id)
            except (tk.TclError, ValueError):
                pass
            self._after_id = None
        self._flush()

    def _flush(self):
        self._after_id = None
        if not self._pending:
            return
        items = self._pending
        self._pending = []

        if len(items) == 1:
            title, message, kind = items[0]
            _KIND_FN.get(kind, messagebox.showinfo)(title, message, parent=self.parent)
            return

        unique_titles = {t for t, _, _ in items}
        max_kind = max(items, key=lambda x: _KIND_RANK.get(x[2], 0))[2]
        if len(unique_titles) == 1:
            title = next(iter(unique_titles))
            body = "\n\n".join(m for _, m, _ in items)
        else:
            title = "Station Alerts"
            body = "\n\n".join(f"[{t}] {m}" for t, m, _ in items)
        _KIND_FN.get(max_kind, messagebox.showinfo)(title, body, parent=self.parent)


# Module-level buffer; call configure_message_buffer(root) once at startup.
_message_buffer = None


def configure_message_buffer(parent, delay_ms=80):
    """Create/replace the global MessageBuffer bound to the main window."""
    global _message_buffer
    _message_buffer = MessageBuffer(parent, delay_ms=delay_ms)
    return _message_buffer


def report_message(title, message, kind="info", parent=None):
    """
    Report via the global buffer when configured; otherwise show immediately.
    parent is used only as fallback when no buffer exists.
    """
    if _message_buffer is not None:
        _message_buffer.report(title, message, kind=kind)
        return
    fn = _KIND_FN.get(kind, messagebox.showinfo)
    fn(title, message, parent=parent)
