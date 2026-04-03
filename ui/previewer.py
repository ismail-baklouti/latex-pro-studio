"""
Latex Pro Studio - PDF Preview Component
High-performance rendering using PyMuPDF (fitz).
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import logging

logger = logging.getLogger(__name__)

class PDFPreviewer(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.doc = None
        self.zoom_scale = 1.3  # Default zoom
        self.pages_refs = []   # Keep references to images to prevent garbage collection
        
        self._setup_ui()

    def _setup_ui(self):
        """Build the previewer interface with scrollbars and canvas."""
        # --- 1. Internal Toolbar ---
        self.controls = ttk.Frame(self, bootstyle=SECONDARY)
        self.controls.pack(side=TOP, fill=X)
        
        ttk.Button(self.controls, text="➕", command=self.zoom_in, bootstyle=LINK).pack(side=LEFT, padx=2)
        ttk.Button(self.controls, text="➖", command=self.zoom_out, bootstyle=LINK).pack(side=LEFT, padx=2)
        self.zoom_label = ttk.Label(self.controls, text="130%", font=("Helvetica", 9), bootstyle=SECONDARY)
        self.zoom_label.pack(side=LEFT, padx=10)
        
        # --- 2. Canvas & Scrollbars ---
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill=BOTH, expand=YES)
        
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=VERTICAL)
        self.v_scroll.pack(side=RIGHT, fill=Y)
        
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient=HORIZONTAL)
        self.h_scroll.pack(side=BOTTOM, fill=X)
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="#525659",
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
            highlightthickness=0
        )
        self.canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Bind MouseWheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.external_btn = ttk.Button(
            self.controls, 
            text="🖥️ Open Externally", 
            command=self._handle_external_open, 
            bootstyle=(INFO, OUTLINE),
            padding=2
        )
        self.external_btn.pack(side=RIGHT, padx=5, pady=2)

    def _handle_external_open(self):
        """Open the current PDF in the default system viewer."""
        if self.doc:
            path = self.doc.name
            try:
                if sys.platform.startswith('darwin'):
                    os.system(f'open "{path}"')
                elif sys.platform == 'win32':
                    os.startfile(path)
                elif sys.platform == 'linux':
                    os.system(f'xdg-open "{path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF externally: {e}")

  

    def display_pdf(self, pdf_path):
        """Renders the PDF onto the canvas."""
        try:
            # Clear old data
            if self.doc:
                self.doc.close()
            self.canvas.delete("all")
            self.pages_refs = []
            
            self.doc = fitz.open(pdf_path)
            y_offset = 10  # Start with a small padding
            
            for page in self.doc:
                # Calculate zoom matrix
                matrix = fitz.Matrix(self.zoom_scale, self.zoom_scale)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                
                # Convert Pixmap to PIL Image then to ImageTk
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)
                self.pages_refs.append(photo)
                
                # Draw on canvas
                # Centering logic: calculate X based on canvas width
                canvas_width = self.canvas.winfo_width()
                x_pos = max(10, (canvas_width - pix.width) // 2)
                
                self.canvas.create_image(x_pos, y_offset, anchor=NW, image=photo)
                y_offset += pix.height + 15  # Add gap between pages
            
            # Update scroll region to cover all pages
            self.canvas.config(scrollregion=(0, 0, pix.width + 40, y_offset))
            self.zoom_label.config(text=f"{int(self.zoom_scale * 100)}%")
            
        except Exception as e:
            logger.error(f"Failed to render PDF: {e}")
            # Silently fail if file is busy (common during LaTeX re-compilation)

    def zoom_in(self):
        if self.zoom_scale < 3.0:
            self.zoom_scale += 0.2
            self._refresh()

    def zoom_out(self):
        if self.zoom_scale > 0.5:
            self.zoom_scale -= 0.2
            self._refresh()

    def _refresh(self):
        """Re-renders current document if available."""
        if self.doc:
            path = self.doc.name
            self.display_pdf(path)

    def _on_mousewheel(self, event):
        """Handle scrolling with mouse wheel."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self):
        """Cleanup."""
        if self.doc:
            self.doc.close()
            self.doc = None
        self.canvas.delete("all")
        self.pages_refs = []