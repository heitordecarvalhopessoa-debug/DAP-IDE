import re
import tkinter as tk

class EditorHighlighter:
    def __init__(self, editor, theme_colors):
        self.editor = editor
        self.theme_colors = theme_colors
        self._setup_tags()

    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        self._setup_tags()
        self.highlight_syntax()

    def _setup_tags(self):
        syntax = self.theme_colors["syntax"]
        self.editor.tag_config("keyword", foreground=syntax["keyword"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("keyboard_kw", foreground=syntax["keyboard_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("table_kw", foreground=syntax["table_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("global_kw", foreground=syntax["global_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("repeat_kw", foreground=syntax["repeat_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("forever_kw", foreground=syntax["forever_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("wait_kw", foreground=syntax["wait_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("type_kw", foreground=syntax["type_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("clear_kw", foreground=syntax["clear_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("cond_kw", foreground=syntax["cond_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("logical_kw", foreground=syntax["logical_kw"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("string", foreground=syntax["string"], font=("Courier New", 11))
        self.editor.tag_config("number", foreground=syntax["number"], font=("Courier New", 11))
        self.editor.tag_config("boolean", foreground=syntax["boolean"], font=("Courier New", 11, "bold"))
        self.editor.tag_config("comment", foreground=syntax["comment"], font=("Courier New", 11, "italic"))

    def highlight_syntax(self):
        for tag in ["keyword", "keyboard_kw", "table_kw", "global_kw", "repeat_kw", "forever_kw", "wait_kw", 
                    "type_kw", "clear_kw", "cond_kw", "logical_kw", "string", "number", 
                    "boolean", "comment"]:
            try:
                self.editor.tag_remove(tag, "1.0", tk.END)
            except Exception:
                pass

        text_content = self.editor.get("1.0", tk.END)
        lines = text_content.split("\n")

        for idx, line in enumerate(lines):
            if "#" in line:
                comment_col = line.index("#")
                self.editor.tag_add("comment", f"{idx + 1}.{comment_col}", f"{idx + 1}.end")
                line = line[:comment_col]

            for kw in ["keyboard", "keycode", "oth"]:
                self._mark_word(line, kw, idx, "keyboard_kw")

            for gkw in ["GLOBAL"]:
                self._mark_word(line, gkw, idx, "global_kw")

            for tkw in ["TABLE"]:
                self._mark_word(line, tkw, idx, "table_kw")

            for kw in ["VAR", "output", "alterate"]:
                self._mark_word(line, kw, idx, "keyword")

            for ckw in ["clear"]:
                self._mark_word(line, ckw, idx, "clear_kw")

            for ckw in ["IF", "ELSEIF", "ELSE"]:
                self._mark_word(line, ckw, idx, "cond_kw")

            for lkw in ["AND", "OR", "NOT", "XOR", "NAND", "NOR", "XNOR"]:
                self._mark_word(line, lkw, idx, "logical_kw")

            for tkw in ["float", "bool", "st", "str", "char", "null"]:
                self._mark_word(line, tkw, idx, "type_kw")

            for rkw in ["repeat"]:
                self._mark_word(line, rkw, idx, "repeat_kw")

            for fkw in ["forever"]:
                self._mark_word(line, fkw, idx, "forever_kw")

            for wkw in ["wait"]:
                self._mark_word(line, wkw, idx, "wait_kw")

            for match in re.finditer(r'("[^"]*")|(\'[^\']*\')', line):
                start, end = match.span()
                self.editor.tag_add("string", f"{idx + 1}.{start}", f"{idx + 1}.{end}")

            for bw in ["true", "false"]:
                start_idx = 0
                while True:
                    pos = line.lower().find(bw, start_idx)
                    if pos == -1:
                        break
                    end_pos = pos + len(bw)
                    self.editor.tag_add("boolean", f"{idx + 1}.{pos}", f"{idx + 1}.{end_pos}")
                    start_idx = end_pos

            for match in re.finditer(r'\b\d+(\.\d+)?\b', line):
                start, end = match.span()
                self.editor.tag_add("number", f"{idx + 1}.{start}", f"{idx + 1}.{end}")

    def _mark_word(self, line, word, line_idx, tag_name):
        start_idx = 0
        while True:
            pos = line.find(word, start_idx)
            if pos == -1:
                break
            end_pos = pos + len(word)
            self.editor.tag_add(tag_name, f"{line_idx + 1}.{pos}", f"{line_idx + 1}.{end_pos}")
            start_idx = end_pos