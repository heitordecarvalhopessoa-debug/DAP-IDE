import time
import tkinter as tk
from tkinter import scrolledtext, ttk

class DAPHelpWindow(tk.Toplevel):
    def __init__(self, parent, section_name, content_text, theme):
        super().__init__(parent)
        self.title(f"DAP Studio Help - {section_name}")
        self.geometry("680x500")
        
        bg = theme["window_bg"]
        fg = theme["editor_fg"]
        editor_bg = theme["editor_bg"]
        
        self.configure(bg=bg)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (680 // 2)
        y = (screen_height // 2) - (500 // 2)
        self.geometry(f"680x500+{x}+{y}")

        header_frame = tk.Frame(self, bg="#000080", height=45)
        header_frame.pack(fill=tk.X)
        
        tk.Label(
            header_frame, 
            text=f"  📖  DAP Documentation: {section_name}", 
            font=("Segoe UI", 11, "bold"), 
            fg="#ffffff", 
            bg="#000080", 
            anchor="w"
        ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        container = tk.Frame(self, bg=editor_bg, bd=1, relief=tk.SOLID)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        text_area = scrolledtext.ScrolledText(
            container, 
            wrap=tk.WORD, 
            font=("Consolas", 10), 
            bg=editor_bg, 
            fg=fg, 
            bd=0, 
            padx=15, 
            pady=15
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, content_text)
        text_area.config(state="disabled")

        footer_frame = tk.Frame(self, bg=bg)
        footer_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Button(
            footer_frame, 
            text="Close Window", 
            command=self.destroy, 
            font=("Segoe UI", 9), 
            bg=theme["btn_bg"], 
            fg=fg,
            relief=tk.RAISED, 
            bd=1, 
            padx=15, 
            pady=5
        ).pack(side=tk.RIGHT)


class DAPTerminalWindow(tk.Toplevel):
    def __init__(self, parent, stop_callback, theme, interpreter_ref=None):
        super().__init__(parent)
        self.title("DAP Execution Output")
        self.geometry("650x400")
        
        bg = theme["window_bg"]
        fg = theme["editor_fg"]
        
        self.configure(bg=bg)
        self.stop_callback = stop_callback
        self.interpreter_ref = interpreter_ref
        self.key_buffer = ""

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (650 // 2)
        y = (screen_height // 2) - (400 // 2)
        self.geometry(f"650x400+{x}+{y}")

        title_bar = tk.Frame(self, bg=theme["sidebar_bg"], height=28)
        title_bar.pack(fill=tk.X)
        
        tk.Label(
            title_bar, 
            text=" ▶ DAP Program Output", 
            font=("Segoe UI", 9, "bold"), 
            fg=fg, 
            bg=theme["sidebar_bg"], 
            anchor="w"
        ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        main_frame = tk.Frame(self, bg=theme["console_bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.console = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD, 
            font=("Courier New", 10), 
            bg=theme["console_bg"], 
            fg=theme["console_fg"], 
            relief=tk.FLAT
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self.console.bind("<Key>", self.on_key_press)
        self.console.focus_set()

        btn_frame = tk.Frame(self, bg=bg)
        btn_frame.pack(fill=tk.X, padx=8, pady=6)

        tk.Button(
            btn_frame, 
            text="Stop Execution", 
            command=self.on_stop, 
            bg="#a93226", 
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"), 
            relief=tk.RAISED, 
            bd=1,
            padx=10
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame, 
            text="Close", 
            command=self.destroy, 
            font=("Segoe UI", 9), 
            bg=theme["btn_bg"], 
            fg=fg,
            relief=tk.RAISED, 
            bd=1,
            padx=10
        ).pack(side=tk.RIGHT, padx=2)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_key_press(self, event):
        if self.interpreter_ref:
            char = event.char if event.char else ""
            keysym = event.keysym.lower()
            
            for tipo, target, block in self.interpreter_ref.key_listeners:
                if tipo == 'KEYBOARD' and char.lower() == target.lower():
                    self.interpreter_ref.execute_block(block)
                elif tipo == 'OTH' and (keysym in target.lower() or char.lower() in target.lower()):
                    self.interpreter_ref.execute_block(block)
                elif tipo == 'KEYCODE':
                    if char:
                        self.key_buffer += char.upper()
                        if len(self.key_buffer) > 20:
                            self.key_buffer = self.key_buffer[-20:]
                        if target.upper() in self.key_buffer:
                            self.interpreter_ref.execute_block(block)
                            self.key_buffer = ""
                            
        return "break"

    def log(self, text):
        self.console.config(state="normal")
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        self.console.config(state="disabled")

    def on_stop(self):
        if self.stop_callback:
            self.stop_callback()
        self.log("[System]: Stop requested.")

    def on_close(self):
        if self.stop_callback:
            self.stop_callback()
        self.destroy()


class DAPSplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Loading DAP Studio...")
        self.geometry("420x220")
        self.overrideredirect(True)
        self.configure(bg="#ffffff", bd=2, relief=tk.RAISED)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (420 // 2)
        y = (screen_height // 2) - (220 // 2)
        self.geometry(f"420x220+{x}+{y}")

        title_bar = tk.Frame(self, bg="#000080", height=22)
        title_bar.pack(fill=tk.X, padx=2, pady=2)
        
        tk.Label(
            title_bar, 
            text=" DAP Studio Setup / Loading...", 
            font=("MS Sans Serif", 9, "bold"), 
            fg="#ffffff", 
            bg="#000080", 
            anchor="w"
        ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        main_frame = tk.Frame(self, bg="#ffffff")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        tk.Label(
            main_frame, 
            text="DAP Studio", 
            font=("Arial", 22, "bold"), 
            fg="#000080", 
            bg="#ffffff"
        ).pack(pady=(5, 2))

        tk.Label(
            main_frame, 
            text="DAP Studio 'Developer Preview 1' ", 
            font=("MS Sans Serif", 8), 
            fg="#666666", 
            bg="#ffffff"
        ).pack(pady=(0, 15))

        self.progress_canvas = tk.Canvas(
            main_frame, 
            width=360, 
            height=20, 
            bg="#ffffff", 
            relief=tk.SUNKEN, 
            bd=2, 
            highlightthickness=0
        )
        self.progress_canvas.pack(pady=5)

        self.status_lbl = tk.Label(
            main_frame, 
            text="Initializing components...", 
            font=("MS Sans Serif", 8), 
            fg="#000000", 
            bg="#ffffff", 
            anchor="w"
        )
        self.status_lbl.pack(fill=tk.X, pady=(5, 0))

    def update_progress(self, percent):
        self.progress_canvas.delete("all")
        num_blocks = int((percent / 100) * 24)
        block_width = 12
        block_gap = 3
        start_x = 3
        
        for i in range(num_blocks):
            x1 = start_x + i * (block_width + block_gap)
            y1 = 3
            x2 = x1 + block_width
            y2 = 17
            self.progress_canvas.create_rectangle(x1, y1, x2, y2, fill="#000080", outline="")

    def animate(self):
        steps = [
            (15, "Loading Lexer..."),
            (40, "Initializing Interpreter..."),
            (70, "Loading User Interface..."),
            (90, "Configuring Workspace..."),
            (100, "Ready!")
        ]
        for val, text in steps:
            self.update_progress(val)
            self.status_lbl.config(text=text)
            self.update()
            time.sleep(0.3)
        self.destroy()