"""
Latex Pro Studio - Syntax Highlighting Editor
Part of: https://github.com/ismail-baklouti/latex-pro-studio
"""

import tkinter as tk
from tkinter import scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import re

class LatexEditor(ttk.Frame):
    def __init__(self, master, font_size=12, **kwargs):
        super().__init__(master, **kwargs)
        
        self.font_family = "Consolas"
        self.font_size = font_size
        
        # --- 1. Text Area ---
        # Using a scrolled text widget for the main editor
        self.text_area = scrolledtext.ScrolledText(
            self, 
            undo=True, 
            autoseparators=True, 
            maxundo=50,
            font=(self.font_family, self.font_size),
            wrap=tk.WORD,
            padx=10,
            pady=10,
            borderwidth=0,
            highlightthickness=0
        )
        self.text_area.pack(fill=BOTH, expand=YES)
        
        # --- 2. Syntax Highlighting Tags ---
        self._setup_tags()
        
        # --- 3. Bindings ---
        self.text_area.bind("<KeyRelease>", self._on_key_release)
        self.text_area.bind("<Control-v>", lambda e: self.after(10, self.highlight_all))
        
        # Callback for citation trigger (to be set by MainWindow)
        self.on_cite_trigger = None

    def _setup_tags(self):
        """Define colors for LaTeX syntax highlighting."""
        # Adjust colors based on theme if necessary
        self.text_area.tag_config("command", foreground="#0056b3", font=(self.font_family, self.font_size, "bold"))
        self.text_area.tag_config("comment", foreground="#808080", font=(self.font_family, self.font_size, "italic"))
        self.text_area.tag_config("bracket", foreground="#a31515")
        self.text_area.tag_config("keyword", foreground="#af00db")
        self.text_area.tag_config("error", background="#ffcccc", foreground="#cc0000")

    def _on_key_release(self, event):
        """Triggered on every key press."""
        # 1. Syntax highlighting for the current line (Performance optimization)
        self.highlight_line()
        
        # 2. Check for citation trigger \cite{
        if event.char == "{":
            # detect common citation commands like \cite{, \citen{, \citet{, \citep{
            content = self.get_text_around_cursor(12)
            triggers = ["\\cite{", "\\citen{", "\\citet{", "\\citep{"]
            for t in triggers:
                if content.endswith(t) and self.on_cite_trigger:
                    self.on_cite_trigger()
                    break

    def get_text_around_cursor(self, length=10):
        """Returns the last 'length' characters before the cursor."""
        idx = self.text_area.index(tk.INSERT)
        start = f"{idx}-{length}c"
        return self.text_area.get(start, idx)

    def highlight_line(self):
        """Highlights syntax only on the current line for speed."""
        line_start = self.text_area.index("insert linestart")
        line_end = self.text_area.index("insert lineend")
        self._apply_highlighting(line_start, line_end)

    def highlight_all(self, event=None):
        """Highlights syntax for the entire document."""
        self._apply_highlighting("1.0", tk.END)

    def _apply_highlighting(self, start, end):
        """Internal logic to run regex and apply tags."""
        content = self.text_area.get(start, end)
        
        # Clear existing tags in the range
        for tag in ["command", "comment", "bracket", "keyword"]:
            self.text_area.tag_remove(tag, start, end)

        # 1. Highlight Comments (% ...)
        for match in re.finditer(r"%.*", content):
            s, e = match.span()
            self.text_area.tag_add("comment", f"{start}+{s}c", f"{start}+{e}c")

        # 2. Highlight Commands (\section, \textbf, etc)
        for match in re.finditer(r"\\[a-zA-Z]+", content):
            s, e = match.span()
            self.text_area.tag_add("command", f"{start}+{s}c", f"{start}+{e}c")

        # 3. Highlight Brackets { } [ ]
        for match in re.finditer(r"[\{\}\[\]]", content):
            s, e = match.span()
            self.text_area.tag_add("bracket", f"{start}+{s}c", f"{start}+{e}c")

        # 4. Highlight Keywords (begin, end)
        for match in re.finditer(r"\\(begin|end)", content):
            s, e = match.span()
            self.text_area.tag_add("keyword", f"{start}+{s}c", f"{start}+{e}c")

    # --- API Methods ---
    def get_text(self):
        return self.text_area.get("1.0", tk.END)

    def set_text(self, content):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", content)
        self.highlight_all()

    def insert_at_cursor(self, text):
        self.text_area.insert(tk.INSERT, text)
        self.highlight_line()

    def clear_errors(self):
        self.text_area.tag_remove("error", "1.0", tk.END)

    def mark_error(self, line_number):
        """Highlight a specific line in red."""
        try:
            start = f"{line_number}.0"
            end = f"{line_number}.end"
            self.text_area.tag_add("error", start, end)
            self.text_area.see(start)
        except:
            pass