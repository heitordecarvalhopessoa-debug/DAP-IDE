import re
import os
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, simpledialog

from .ui_components import DAPHelpWindow, DAPTerminalWindow, DAPSplashScreen
from .editor_highlighter import EditorHighlighter
from .theme_manager import THEMES

class DAPIDE(tk.Tk):
    def __init__(self, run_callback_factory):
        super().__init__()
        self.withdraw()
        
        splash = DAPSplashScreen(self)
        splash.animate()
        
        self.deiconify()
        self.title("DAP Studio")
        self.geometry("1100x600")
        self.run_callback_factory = run_callback_factory
        self.open_files = {}
        self.file_modified = {}
        self.current_file = None
        self.workspace_dir = None
        self.stop_requested = False
        self.running_thread = None
        self.active_terminal_window = None
        
        self.current_theme_name = "Bright"
        self.theme = THEMES[self.current_theme_name]
        
        self.output_queue = queue.Queue()

        self.configure(bg=self.theme["window_bg"], bd=2, relief=tk.RAISED)
        self.create_widgets()
        self.bind_shortcuts()
        self.select_folder_startup()
        self.process_output_queue()

    def bind_shortcuts(self):
        self.bind("<Control-s>", lambda e: self.save_current_file())
        self.bind("<Control-S>", lambda e: self.save_current_file())
        self.bind("<Control-n>", lambda e: self.create_new_dap_file())
        self.bind("<Control-N>", lambda e: self.create_new_dap_file())
        self.bind("<Control-o>", lambda e: self.select_folder())
        self.bind("<Control-O>", lambda e: self.select_folder())

    def create_widgets(self):
        self.menubar = tk.Menu(self, bg=self.theme["window_bg"], fg=self.theme["editor_fg"], activebackground="#316ac5", activeforeground="#ffffff", relief=tk.FLAT)
        
        file_menu = tk.Menu(self.menubar, tearoff=0, bg=self.theme["editor_bg"], fg=self.theme["editor_fg"], activebackground="#316ac5", activeforeground="#ffffff")
        file_menu.add_command(label="New File (Ctrl+N)", command=self.create_new_dap_file)
        file_menu.add_command(label="Open Folder... (Ctrl+O)", command=self.select_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Save File (Ctrl+S)", command=self.save_current_file)
        file_menu.add_command(label="Run DAP", command=self.trigger_run)
        file_menu.add_command(label="Stop DAP", command=self.trigger_stop)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(self.menubar, tearoff=0, bg=self.theme["editor_bg"], fg=self.theme["editor_fg"], activebackground="#316ac5", activeforeground="#ffffff")
        tools_menu.add_command(label="New .dap File", command=self.create_new_dap_file)
        tools_menu.add_separator()
        tools_menu.add_command(label="Format Code", command=self.format_code)
        tools_menu.add_command(label="Environment Info", command=self.show_environment_info)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)

        themes_menu = tk.Menu(self.menubar, tearoff=0, bg=self.theme["editor_bg"], fg=self.theme["editor_fg"], activebackground="#316ac5", activeforeground="#ffffff")
        themes_menu.add_command(label="☀️ Bright", command=lambda: self.change_theme("Bright"))
        themes_menu.add_command(label="🌙 Dark", command=lambda: self.change_theme("Dark"))
        themes_menu.add_command(label="👁️ High Contrast", command=lambda: self.change_theme("High Contrast"))
        themes_menu.add_command(label="⚡ Cyberpunk", command=lambda: self.change_theme("Cyberpunk"))
        themes_menu.add_command(label="❄️ Nord", command=lambda: self.change_theme("Nord"))
        themes_menu.add_command(label="🔥 Monokai", command=lambda: self.change_theme("Monokai"))
        self.menubar.add_cascade(label="Themes", menu=themes_menu)

        help_menu = tk.Menu(self.menubar, tearoff=0, bg=self.theme["editor_bg"], fg=self.theme["editor_fg"], activebackground="#316ac5", activeforeground="#ffffff")
        help_menu.add_command(label="Documentation", command=self.open_help_documentation)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.open_help_shortcuts)
        help_menu.add_command(label="About DAP Studio", command=self.open_help_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=self.menubar)

        self.root_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=self.theme["window_bg"], sashwidth=5, relief=tk.SUNKEN, bd=2)
        self.root_pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.sidebar_frame = tk.Frame(self.root_pane, bg=self.theme["sidebar_bg"], relief=tk.SUNKEN, borderwidth=1)
        self.root_pane.add(self.sidebar_frame, width=280)

        side_header = tk.Frame(self.sidebar_frame, bg="#000080", height=24)
        side_header.pack(fill=tk.X)
        tk.Label(side_header, text=" PROJECT EXPLORER ", bg="#000080", fg="#ffffff", anchor="w", font=("MS Sans Serif", 8, "bold")).pack(side=tk.LEFT, padx=4)

        self.btn_box = tk.Frame(self.sidebar_frame, bg=self.theme["sidebar_bg"], relief=tk.RAISED, bd=1)
        self.btn_box.pack(fill=tk.X, padx=4, pady=4)
        
        self.sidebar_buttons = []
        self.btn_new = tk.Button(self.btn_box, text="+ New", command=self.create_new_dap_file, font=("MS Sans Serif", 8), bg=self.theme["btn_bg"], fg=self.theme["sidebar_fg"], relief=tk.RAISED, bd=2)
        self.btn_new.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1, pady=1)
        self.sidebar_buttons.append(self.btn_new)

        self.btn_open = tk.Button(self.btn_box, text="📁 Open", command=self.select_folder, font=("MS Sans Serif", 8), bg=self.theme["btn_bg"], fg=self.theme["sidebar_fg"], relief=tk.RAISED, bd=2)
        self.btn_open.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1, pady=1)
        self.sidebar_buttons.append(self.btn_open)

        self.btn_run = tk.Button(self.btn_box, text="▶ Run", command=self.trigger_run, bg="#e0ffe0", fg="#000000", font=("MS Sans Serif", 8, "bold"), relief=tk.RAISED, bd=2)
        self.btn_run.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1, pady=1)

        self.btn_stop = tk.Button(self.btn_box, text="⏹ Stop", command=self.trigger_stop, bg="#ffe0e0", fg="#000000", font=("MS Sans Serif", 8, "bold"), relief=tk.RAISED, bd=2)
        self.btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1, pady=1)

        self.tree_frame = tk.Frame(self.sidebar_frame, bg=self.theme["tree_bg"], relief=tk.SUNKEN, bd=2)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background=self.theme["tree_bg"], foreground=self.theme["tree_fg"], fieldbackground=self.theme["tree_bg"], borderwidth=0)
        self.style.map("Treeview", background=[('selected', self.theme["tree_select"])], foreground=[('selected', '#ffffff')])

        self.tree = ttk.Treeview(self.tree_frame, selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.bind("<Double-1>", self.on_file_double_click)

        editor_frame = tk.Frame(self.root_pane, bg=self.theme["window_bg"])
        self.root_pane.add(editor_frame)
        
        self.tab_bar_frame = tk.Frame(editor_frame, bg=self.theme["window_bg"], height=28)
        self.tab_bar_frame.pack(fill=tk.X)
        self.tab_buttons = {}

        editor_container = tk.Frame(editor_frame, relief=tk.SUNKEN, bd=2)
        editor_container.pack(fill=tk.BOTH, expand=True)

        self.welcome_frame = tk.Frame(editor_container, bg=self.theme["editor_bg"])
        self.welcome_inner = tk.Frame(self.welcome_frame, bg=self.theme["editor_bg"])
        self.welcome_inner.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        title_container = tk.Frame(self.welcome_inner, bg=self.theme["editor_bg"])
        title_container.pack(pady=(0, 2))
        
        self.lbl_d = tk.Label(title_container, text="D", font=("Arial", 32, "bold"), fg="#ff3333", bg=self.theme["editor_bg"])
        self.lbl_d.pack(side=tk.LEFT)
        self.lbl_a = tk.Label(title_container, text="A", font=("Arial", 32, "bold"), fg="#33cc33", bg=self.theme["editor_bg"])
        self.lbl_a.pack(side=tk.LEFT)
        self.lbl_p = tk.Label(title_container, text="P", font=("Arial", 32, "bold"), fg="#3366ff", bg=self.theme["editor_bg"])
        self.lbl_p.pack(side=tk.LEFT)
        self.lbl_studio = tk.Label(title_container, text=" Studio", font=("Arial", 28, "bold"), fg=self.theme["editor_fg"], bg=self.theme["editor_bg"])
        self.lbl_studio.pack(side=tk.LEFT)

        self.lbl_welcome_sub = tk.Label(self.welcome_inner, text="Developer Preview 1", font=("MS Sans Serif", 9), fg=self.theme["line_num_fg"], bg=self.theme["editor_bg"])
        self.lbl_welcome_sub.pack(pady=(0, 25))
        
        self.welcome_buttons = []
        btn_style = {"font": ("MS Sans Serif", 9), "bg": self.theme["btn_bg"], "fg": self.theme["editor_fg"], "relief": tk.RAISED, "bd": 2, "width": 26, "anchor": "w"}
        
        self.wb1 = tk.Button(self.welcome_inner, text="📁  Open Workspace Folder... (Ctrl+O)", command=self.select_folder, **btn_style)
        self.wb1.pack(pady=4, fill=tk.X)
        self.welcome_buttons.append(self.wb1)

        self.wb2 = tk.Button(self.welcome_inner, text="📄  Create New File... (Ctrl+N)", command=self.create_new_dap_file, **btn_style)
        self.wb2.pack(pady=4, fill=tk.X)
        self.welcome_buttons.append(self.wb2)

        self.wb3 = tk.Button(self.welcome_inner, text="📖  View Documentation", command=self.open_help_documentation, **btn_style)
        self.wb3.pack(pady=4, fill=tk.X)
        self.welcome_buttons.append(self.wb3)

        self.editor_sub_frame = tk.Frame(editor_container, bg=self.theme["editor_bg"])

        self.line_numbers = tk.Text(self.editor_sub_frame, width=4, padx=4, takefocus=0, border=0, background=self.theme["line_num_bg"], foreground=self.theme["line_num_fg"], font=("Courier New", 11), state="disabled")
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = scrolledtext.Text(self.editor_sub_frame, wrap=tk.WORD, font=("Courier New", 11), bg=self.theme["editor_bg"], fg=self.theme["editor_fg"], insertbackground=self.theme["editor_fg"], relief=tk.FLAT)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.highlighter = EditorHighlighter(self.editor, self.theme)

        self.editor.bind("<Tab>", self.handle_tab)
        self.editor.bind("<Return>", self.handle_return)
        self.editor.bind("<KeyRelease>", self.on_text_modified)
        self.editor.bind("<MouseWheel>", self.update_line_numbers)
        self.editor.bind("<Button-4>", self.update_line_numbers)
        self.editor.bind("<Button-5>", self.update_line_numbers)
        self.editor.bind("<Down>", self.navigate_suggestions)
        self.editor.bind("<Up>", self.navigate_suggestions)

        self.suggestion_box = tk.Listbox(editor_container, font=("Courier New", 10), bg="#ffffe1", fg="#000000", selectbackground="#316ac5", selectforeground="#ffffff", relief=tk.SOLID, borderwidth=1)
        self.suggestion_window = None

        self.completions = [
            ("⚙️ GLOBAL", "GLOBAL "), 
            ("⚙️ VAR", "VAR "), 
            ("⚙️ TABLE", "TABLE [\n   \n]"),

            ("🖥️ alterate", "alterate()"), 
            ("🖥️ output", "output()"), 
            ("🖥️ wait", "wait()"), 
            
            ("🔁 repeat", "repeat() [\n   \n]"), 
            ("🔁 forever", "forever [\n   \n]"),
            
            ("🔀 IF", "IF () [\n   \n]"), 
            ("🔀 ELSEIF", "ELSEIF () [\n   \n]"), 
            ("🔀 ELSE", "ELSE [\n   \n]"),
            
            ("🔣 AND", " AND "), 
            ("🔣 OR", " OR "), 
            ("🔣 NOT", " NOT "), 
            ("🔣 XOR", " XOR "),
            ("🔣 NAND", " NAND "),
            ("🔣 NOR", " NOR "),
            ("🔣 XNOR", " XNOR "),

            ("📌 float", "float()"), 
            ("📌 st", "st()"), 
            ("📌 bool", "bool()"), 
            ("📌 char", "char()"), 
            ("📌 null", "null()"),
            ("📌 random", "random(1, 10)"),

            ("⌨️ keyboard", "keyboard(\"a\") [\n   \n]"), 
            ("⌨️ keycode", "keycode(\"ENTER\") [\n   \n]"), 
            ("⌨️ oth", "oth(\"space\") [\n   \n]"),

            ("✅ true", "true"), 
            ("❌ false", "false"),
            ("🧹 clear", "clear()")
        ]

        self.show_welcome_screen()

    def change_theme(self, theme_name):
        if theme_name in THEMES:
            self.current_theme_name = theme_name
            self.theme = THEMES[theme_name]
            
            self.configure(bg=self.theme["window_bg"])
            self.root_pane.config(bg=self.theme["window_bg"])
            self.sidebar_frame.config(bg=self.theme["sidebar_bg"])
            self.btn_box.config(bg=self.theme["sidebar_bg"])
            self.tree_frame.config(bg=self.theme["tree_bg"])
            self.tab_bar_frame.config(bg=self.theme["window_bg"])
            
            self.style.configure("Treeview", background=self.theme["tree_bg"], foreground=self.theme["tree_fg"], fieldbackground=self.theme["tree_bg"])
            self.style.map("Treeview", background=[('selected', self.theme["tree_select"])])

            for btn in self.sidebar_buttons:
                btn.config(bg=self.theme["btn_bg"], fg=self.theme["sidebar_fg"])

            self.welcome_frame.config(bg=self.theme["editor_bg"])
            self.welcome_inner.config(bg=self.theme["editor_bg"])
            self.lbl_studio.config(bg=self.theme["editor_bg"], fg=self.theme["editor_fg"])
            self.lbl_welcome_sub.config(bg=self.theme["editor_bg"], fg=self.theme["line_num_fg"])
            for btn in self.welcome_buttons:
                btn.config(bg=self.theme["btn_bg"], fg=self.theme["editor_fg"])

            self.editor_sub_frame.config(bg=self.theme["editor_bg"])
            self.editor.config(bg=self.theme["editor_bg"], fg=self.theme["editor_fg"], insertbackground=self.theme["editor_fg"])
            self.line_numbers.config(background=self.theme["line_num_bg"], foreground=self.theme["line_num_fg"])
            
            self.highlighter.update_theme(self.theme)
            self.update_tab_bar()

    def show_welcome_screen(self):
        self.editor_sub_frame.pack_forget()
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)

    def hide_welcome_screen(self):
        self.welcome_frame.pack_forget()
        self.editor_sub_frame.pack(fill=tk.BOTH, expand=True)

    def handle_tab(self, event):
        if self.suggestion_window:
            self.complete_suggestion(event)
        else:
            self.editor.insert(tk.INSERT, "   ")
        return "break"

    def handle_return(self, event):
        if self.suggestion_window:
            self.complete_suggestion(event)
            return "break"
            
        current_line_idx = self.editor.index(tk.INSERT).split(".")[0]
        line_text = self.editor.get(f"{current_line_idx}.0", f"{current_line_idx}.end").strip()
        
        block_keywords = ("forever", "repeat", "if", "else", "elseif", "table", "TABLE", "IF", "ELSEIF", "ELSE", "keyboard", "keycode", "oth")
        is_block_start = line_text.endswith("[") or (any(line_text.startswith(kw) for kw in block_keywords) and line_text.endswith("["))
        
        if is_block_start:
            self.editor.insert(tk.INSERT, "\n   \n]")
            self.editor.mark_set(tk.INSERT, f"{int(current_line_idx)+1}.3")
            self.highlighter.highlight_syntax()
            self.update_line_numbers()
            return "break"
        
        return None

    def select_folder_startup(self):
        folder = filedialog.askdirectory(title="Select DAP Studio Workspace Folder")
        if folder:
            self.load_directory(folder)
        else:
            self.workspace_dir = os.getcwd()
            self.load_directory(self.workspace_dir)

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.workspace_dir if self.workspace_dir else os.getcwd())
        if folder:
            self.load_directory(folder)

    def load_directory(self, path):
        self.workspace_dir = path
        self.tree.delete(*self.tree.get_children())
        folder_name = os.path.basename(path) or path
        self.tree.heading("#0", text=folder_name, anchor="w")
        
        try:
            items = os.listdir(path)
            for item in sorted(items):
                if item.startswith('.'): continue
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    node = self.tree.insert("", tk.END, text=item, values=[full_path])
                    self.load_sub_directory(node, full_path)
                elif item.endswith('.dap'):
                    self.tree.insert("", tk.END, text=item, values=[full_path])
        except Exception:
            pass

    def load_sub_directory(self, parent, path):
        try:
            items = os.listdir(path)
            for item in sorted(items):
                if item.startswith('.'): continue
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    node = self.tree.insert(parent, tk.END, text=item, values=[full_path])
                    self.load_sub_directory(node, full_path)
                elif item.endswith('.dap'):
                    self.tree.insert(parent, tk.END, text=item, values=[full_path])
        except Exception:
            pass

    def update_tab_bar(self):
        for widget in self.tab_bar_frame.winfo_children():
            widget.destroy()
        
        self.tab_buttons.clear()
        
        for path in self.open_files:
            filename = os.path.basename(path)
            if self.file_modified.get(path, False):
                filename += " *"
            is_active = (path == self.current_file)
            bg_color = self.theme["tab_active"] if is_active else self.theme["tab_inactive"]
            fg_color = self.theme["editor_fg"] if is_active else (self.theme["line_num_fg"] if self.current_theme_name != "Bright" else "#666666")
            relief_style = tk.RAISED if is_active else tk.FLAT
            
            tab_frame = tk.Frame(self.tab_bar_frame, bg=bg_color, relief=relief_style, borderwidth=1)
            tab_frame.pack(side=tk.LEFT, padx=1, pady=2)
            
            btn = tk.Button(tab_frame, text=filename, bg=bg_color, fg=fg_color, font=("MS Sans Serif", 8), relief=tk.FLAT, command=lambda p=path: self.switch_to_file(p))
            btn.pack(side=tk.LEFT, padx=(4, 2))
            
            close_btn = tk.Button(tab_frame, text="×", bg=bg_color, fg=fg_color, font=("MS Sans Serif", 8, "bold"), relief=tk.FLAT, command=lambda p=path: self.close_file(p))
            close_btn.pack(side=tk.LEFT, padx=(0, 4))

    def switch_to_file(self, path):
        if self.current_file:
            self.open_files[self.current_file] = self.editor.get("1.0", tk.END)
            
        self.hide_welcome_screen()
        self.current_file = path
        content = self.open_files.get(path, "")
        self.editor.delete("1.0", tk.END)
        self.editor.insert(tk.END, content)
        self.highlighter.highlight_syntax()
        self.update_line_numbers()
        self.update_tab_bar()

    def close_file(self, path):
        if path in self.open_files:
            del self.open_files[path]
        if path in self.file_modified:
            del self.file_modified[path]
        
        if self.current_file == path:
            self.current_file = None
            self.editor.delete("1.0", tk.END)
            self.update_line_numbers()
            if self.open_files:
                next_path = list(self.open_files.keys())[0]
                self.switch_to_file(next_path)
            else:
                self.show_welcome_screen()
        
        self.update_tab_bar()

    def on_file_double_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item: return
        item_values = self.tree.item(selected_item, "values")
        if item_values:
            file_path = item_values[0]
            if os.path.isfile(file_path) and file_path.endswith('.dap'):
                if file_path not in self.open_files:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        self.open_files[file_path] = content
                        self.file_modified[file_path] = False
                    except Exception:
                        self.open_files[file_path] = ""
                        self.file_modified[file_path] = False
                
                self.switch_to_file(file_path)

    def create_new_dap_file(self):
        filename = simpledialog.askstring("New DAP File", "File name (e.g., test.dap):")
        if filename:
            if not filename.endswith('.dap'):
                filename += '.dap'
            base_dir = self.workspace_dir if self.workspace_dir else os.getcwd()
            filepath = os.path.join(base_dir, filename)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write('')
                self.load_directory(base_dir)
                self.open_files[filepath] = ''
                self.file_modified[filepath] = False
                self.switch_to_file(filepath)
            except Exception:
                pass

    def save_current_file(self):
        if self.current_file:
            try:
                self.open_files[self.current_file] = self.editor.get("1.0", tk.END)
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(self.open_files[self.current_file])
                self.file_modified[self.current_file] = False
                self.update_tab_bar()
                self.log_output(f"[System]: File '{os.path.basename(self.current_file)}' saved successfully.")
            except Exception as e:
                self.log_output(f"[Error saving file]: {e}")

    def format_code(self):
        if not self.current_file: return
        code = self.editor.get("1.0", tk.END)
        lines = code.split("\n")
        formatted_lines = []
        indent_level = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append("")
                continue
            if stripped == "]":
                indent_level = max(0, indent_level - 1)
            formatted_lines.append("   " * indent_level + stripped)
            if stripped.endswith("["):
                indent_level += 1
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", "\n".join(formatted_lines))
        self.highlighter.highlight_syntax()
        self.update_line_numbers()
        self.log_output("[Tools]: Code formatted successfully.")

    def show_environment_info(self):
        self.log_output("=== DAP STUDIO ENVIRONMENT INFO ===")
        self.log_output(f"Workspace Directory: {self.workspace_dir}")
        self.log_output(f"Active File: {self.current_file}")
        self.log_output(f"Open Files Count: {len(self.open_files)}")
        self.log_output(f"Current Theme: {self.current_theme_name}")
        self.log_output("===================================")

    def open_help_documentation(self):
        doc_text = """=== DAP SYNTAX DOCUMENTATION ===

1. VARIABLES & CONSTANTS
- VAR name = value : Declare local variable.
- GLOBAL name = value : Declare immutable global variable.
- name = value : Direct variable reassignment.
- clear(name) : Clears the variable and sets its value to null().
- alterate(name, value) : Update existing variable value.
- random(min, max) : Generate a random integer between min and max.

2. KEYBOARD LISTENERS
- keyboard("a") [ ... ] : Triggers when character 'a' is pressed.
- keycode("ENTER") [ ... ] : Triggers when key sequence/code is typed.
- oth("space") [ ... ] : Triggers on special keys or characters.
"""
        DAPHelpWindow(self, "Documentation", doc_text, self.theme)

    def open_help_shortcuts(self):
        shortcuts_text = """=== DAP STUDIO SHORTCUTS ===

- TAB : Inserts 3 spaces.
- ENTER (on blocks) : Auto-indents and closes brackets.
- CTRL + S : Save current file.
- CTRL + N : Create new file.
- CTRL + O : Open folder.
"""
        DAPHelpWindow(self, "Shortcuts", shortcuts_text, self.theme)

    def open_help_about(self):
        about_text = """=== ABOUT DAP STUDIO ===

DAP Studio - Developer Preview 1
A classic retro-styled Integrated Development Environment (IDE) built for writing, debugging, and running DAP scripts.
"""
        DAPHelpWindow(self, "About", about_text, self.theme)

    def update_line_numbers(self, event=None):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", tk.END)
        
        end_index = self.editor.index("end-1c")
        num_lines = int(end_index.split(".")[0])
        line_string = "\n".join(str(i) for i in range(1, num_lines + 1))
        
        self.line_numbers.insert(tk.END, line_string)
        self.line_numbers.config(state="disabled")
        try:
            self.line_numbers.yview_moveto(self.editor.yview()[0])
        except Exception:
            pass

    def on_text_modified(self, event):
        self.highlighter.highlight_syntax()
        self.update_line_numbers()
        if self.current_file:
            self.open_files[self.current_file] = self.editor.get("1.0", tk.END)
            self.file_modified[self.current_file] = True
            self.update_tab_bar()

        if event.keysym in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return

        current_line_idx = self.editor.index(tk.INSERT).split(".")[0]
        line_text = self.editor.get(f"{current_line_idx}.0", tk.INSERT)
        word_match = re.search(r'[a-zA-Z_]\w*$', line_text)

        code_text = self.editor.get("1.0", tk.END)
        declared_names = re.findall(r'(?:VAR|GLOBAL|TABLE)\s+([a-zA-Z_]\w*)', code_text)
        sub_declared = re.findall(r'^\s+(?:VAR|GLOBAL)\s+([a-zA-Z_]\w*)', code_text, re.MULTILINE)
        all_declared = list(set(declared_names + sub_declared))
        
        dynamic_completions = self.completions.copy()
        for name in all_declared:
            dynamic_completions.append((f"📦 {name}", name))

        if word_match:
            typed_word = word_match.group(0).lower()
            matches = [item for item in dynamic_completions if typed_word in item[1].lower()]
            
            if matches:
                self.show_suggestions(matches)
            else:
                self.hide_suggestions()
        else:
            self.hide_suggestions()

    def show_suggestions(self, matches):
        self.suggestion_box.delete(0, tk.END)
        for label, snippet in matches:
            self.suggestion_box.insert(tk.END, label)
            
        if not self.suggestion_window:
            bbox = self.editor.bbox(tk.INSERT)
            if bbox:
                x, y, _, h = bbox
                self.suggestion_box.place(x=x, y=y + h, width=180, height=100)
                self.suggestion_window = True
                self.suggestion_box.selection_set(0)

    def hide_suggestions(self):
        if self.suggestion_window:
            self.suggestion_box.place_forget()
            self.suggestion_window = None

    def navigate_suggestions(self, event):
        if self.suggestion_window:
            size = self.suggestion_box.size()
            if size == 0:
                return "break"
            selection = self.suggestion_box.curselection()
            index = selection[0] if selection else 0
            
            if event.keysym == "Down":
                index = (index + 1) % size
            elif event.keysym == "Up":
                index = (index - 1 + size) % size
                
            self.suggestion_box.selection_clear(0, tk.END)
            self.suggestion_box.selection_set(index)
            self.suggestion_box.see(index)
            return "break"

    def complete_suggestion(self, event):
        if self.suggestion_window:
            selection = self.suggestion_box.curselection()
            if selection:
                index = selection[0]
                selected_label = self.suggestion_box.get(index)
                
                code_text = self.editor.get("1.0", tk.END)
                declared_names = re.findall(r'(?:VAR|GLOBAL|TABLE)\s+([a-zA-Z_]\w*)', code_text)
                sub_declared = re.findall(r'^\s+(?:VAR|GLOBAL)\s+([a-zA-Z_]\w*)', code_text, re.MULTILINE)
                all_declared = list(set(declared_names + sub_declared))
                dynamic_completions = self.completions.copy()
                for name in all_declared:
                    dynamic_completions.append((f"📦 {name}", name))
                
                snippet = next(s for l, s in dynamic_completions if l == selected_label)
                
                current_line_idx = self.editor.index(tk.INSERT).split(".")[0]
                line_text = self.editor.get(f"{current_line_idx}.0", tk.INSERT)
                word_match = re.search(r'[a-zA-Z_]\w*$', line_text)
                if word_match:
                    start_col = word_match.start()
                    self.editor.delete(f"{current_line_idx}.{start_col}", tk.INSERT)
                    
                self.editor.insert(tk.INSERT, snippet)
                self.hide_suggestions()
                return "break"

    def log_output(self, text):
        if self.active_terminal_window and self.active_terminal_window.winfo_exists():
            self.active_terminal_window.log(text)

    def process_output_queue(self):
        try:
            while True:
                text = self.output_queue.get_nowait()
                if self.active_terminal_window and self.active_terminal_window.winfo_exists():
                    self.active_terminal_window.log(text)
        except queue.Empty:
            pass
        self.after(50, self.process_output_queue)

    def trigger_stop(self):
        self.stop_requested = True

    def trigger_run(self):
        if self.current_file:
            try:
                self.open_files[self.current_file] = self.editor.get("1.0", tk.END)
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(self.open_files[self.current_file])
                self.file_modified[self.current_file] = False
                self.update_tab_bar()
            except Exception:
                pass
                
        if self.active_terminal_window and self.active_terminal_window.winfo_exists():
            self.active_terminal_window.destroy()

        self.active_terminal_window = DAPTerminalWindow(self, self.trigger_stop, self.theme)
        
        code = self.editor.get("1.0", tk.END)
        self.stop_requested = False

        if self.running_thread and self.running_thread.is_alive():
            return

        def check_stop():
            return self.stop_requested

        def register_interpreter(interpreter):
            if self.active_terminal_window and self.active_terminal_window.winfo_exists():
                self.active_terminal_window.interpreter_ref = interpreter

        def thread_target():
            self.run_callback_factory(code, self.log_output, check_stop, register_interpreter)

        self.running_thread = threading.Thread(target=thread_target, daemon=True)
        self.running_thread.start()