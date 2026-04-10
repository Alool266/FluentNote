import customtkinter as ctk
import pyperclip
import os
import json
import re
from tkinter import Toplevel
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

FILE_PATH = "sticky_note.txt"
SAVE_DEBOUNCE_MS = 500


class StickyNoteApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("320x400")
        self.minsize(320, 250)
        self.resizable(True, True)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        self.configure(fg_color="#2b2b2b")
        
        try:
            import sys
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'icon.png')
            else:
                icon_path = "icon.png"
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.tk.call('wm', 'iconphoto', self._w, img)
        except Exception as e:
            print(f"Icon error: {e}")

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 320
        y = 20
        self.geometry(f"300x400+{x}+{y}")

        self.text_area = None
        self.copy_button = None
        self.close_button = None
        self.save_timer = None
        self.task_mode = False

        self.create_ui()
        self.load_saved_content()
        self.bind_events()
        self.show_welcome()

    def show_welcome(self):
        import configparser
        config = configparser.ConfigParser()
        config_file = "settings.ini"
        
        first_run = True
        if os.path.exists(config_file):
            config.read(config_file)
            if config.has_section("App") and config.has_option("App", "first_run"):
                first_run = config.get("App", "first_run") == "True"
        
        if first_run:
            welcome_window = ctk.CTkToplevel(self)
            welcome_window.title("Welcome")
            welcome_window.geometry("300x180")
            welcome_window.resizable(False, False)
            welcome_window.overrideredirect(True)
            welcome_window.attributes("-topmost", True)
            welcome_window.lift()
            welcome_window.focus_force()
            
            x = self.winfo_x() + (self.winfo_width() // 2) - 150
            y = self.winfo_y() + (self.winfo_height() // 2) - 90
            welcome_window.geometry(f"300x180+{x}+{y}")
            
            def close_welcome():
                config = configparser.ConfigParser()
                config.add_section("App")
                config.set("App", "first_run", "False")
                with open(config_file, "w") as f:
                    config.write(f)
                welcome_window.destroy()
            
            close_welcome_btn = ctk.CTkButton(
                welcome_window,
                text="✕",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color="#c42b2b",
                text_color="#a0a0a0",
                font=ctk.CTkFont(size=14),
                command=close_welcome
            )
            close_welcome_btn.place(x=265, y=0)
            
            welcome_label = ctk.CTkLabel(
                welcome_window,
                text="Welcome to FluentNote!",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            welcome_label.pack(pady=(30, 10))
            
            desc_label = ctk.CTkLabel(
                welcome_window,
                text="A modern sticky note app with\nDev Pack features.\n\nEnjoy!",
                font=ctk.CTkFont(size=11),
                justify="center"
            )
            desc_label.pack(pady=10)
            
            welcome_window.bind("<Escape>", lambda e: close_welcome())

    def create_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="#1f1f1f", height=38, corner_radius=0)
        self.header.pack(fill="x", padx=0, pady=0)
        self.header.pack_propagate(False)

        title_label = ctk.CTkLabel(
            self.header,
            text="Sticky Note",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#a0a0a0"
        )
        title_label.pack(side="left", padx=(6, 0), pady=0)

        dev_label = ctk.CTkLabel(
            self.header,
            text="Ali Hasan",
            font=ctk.CTkFont(size=8),
            text_color="#505050"
        )
        dev_label.pack(side="left", padx=(4, 0), pady=0)

        self.search_entry = ctk.CTkEntry(
            self.header,
            placeholder_text="Search...",
            width=70,
            height=22,
            font=ctk.CTkFont(size=9)
        )
        self.search_entry.pack(side="left", padx=(6, 0), pady=0)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        self.close_button = ctk.CTkButton(
            self.header,
            text="✕",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color="#c42b2b",
            text_color="#a0a0a0",
            font=ctk.CTkFont(size=11),
            command=self.close_app
        )
        self.close_button.pack(side="right", padx=(0, 1), pady=0)

        self.settings_button = ctk.CTkButton(
            self.header,
            text="⚙",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color="#a0a0a0",
            font=ctk.CTkFont(size=11),
            command=self.show_settings
        )
        self.settings_button.pack(side="right", padx=(0, 1), pady=0)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)

        dev_pack_frame = ctk.CTkFrame(main_frame, fg_color="#2b2b2b", width=70)
        dev_pack_frame.pack(side="left", fill="y", padx=(0, 0), pady=0)
        dev_pack_frame.pack_propagate(False)

        dev_label = ctk.CTkLabel(
            dev_pack_frame,
            text="Dev Pack",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#707070"
        )
        dev_label.pack(pady=(15, 8))

        json_btn = ctk.CTkButton(
            dev_pack_frame,
            text="JSON",
            font=ctk.CTkFont(size=10),
            height=28,
            corner_radius=8,
            command=self.format_json
        )
        json_btn.pack(pady=2, padx=15, fill="x")

        list_btn = ctk.CTkButton(
            dev_pack_frame,
            text="List",
            font=ctk.CTkFont(size=10),
            height=28,
            corner_radius=8,
            command=self.listify
        )
        list_btn.pack(pady=2, padx=15, fill="x")

        clear_btn = ctk.CTkButton(
            dev_pack_frame,
            text="Clear",
            font=ctk.CTkFont(size=10),
            height=28,
            corner_radius=8,
            command=self.clean
        )
        clear_btn.pack(pady=2, padx=15, fill="x")

        task_btn = ctk.CTkButton(
            dev_pack_frame,
            text="Tasks",
            font=ctk.CTkFont(size=9),
            height=24,
            corner_radius=6,
            command=self.toggle_task_mode
        )
        task_btn.pack(pady=1, padx=15, fill="x")

        self.text_area = ctk.CTkTextbox(
            main_frame,
            font=ctk.CTkFont(size=14),
            fg_color="#2b2b2b",
            text_color="#ffffff",
            border_color="#3a3a3a",
            border_width=1,
            corner_radius=0,
            undo=True
        )
        self.text_area.pack(fill="both", expand=True, padx=(10, 10), pady=10)

        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))

        footer_frame.grid_columnconfigure(0, weight=1)

        opacity_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        opacity_frame.grid(row=0, column=0)

        opacity_label = ctk.CTkLabel(
            opacity_frame,
            text="α",
            font=ctk.CTkFont(size=11),
            text_color="#808080"
        )
        opacity_label.pack(side="left")

        self.opacity_slider = ctk.CTkSlider(
            opacity_frame,
            from_=50,
            to=100,
            number_of_steps=50,
            command=self.on_opacity_change,
            width=80
        )
        self.opacity_slider.set(90)
        self.opacity_slider.pack(side="left", padx=(5, 0))

        self.resize_grip = ctk.CTkLabel(
            self,
            text="⋰⋰",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#808080",
            cursor="sb_h_double_arrow"
        )
        self.resize_grip.place(relx=1.0, rely=1.0, x=-18, y=-18, anchor="se")
        self.resize_grip.lift()

    def load_saved_content(self):
        if os.path.exists(FILE_PATH):
            try:
                with open(FILE_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.text_area.insert("1.0", content)
            except Exception as e:
                print(f"Error loading file: {e}")

    def bind_events(self):
        self.text_area.bind("<<Modified>>", self.on_text_change)
        self.text_area.bind("<Button-1>", self.on_text_click)
        self.text_area.bind("<ButtonRelease-1>", self.on_text_select)

        self.text_area.bind("<Control-a>", self.select_all)
        self.text_area.bind("<Control-A>", self.select_all)
        self.text_area.bind("<Control-z>", self.do_undo)
        self.text_area.bind("<Control-Z>", self.do_undo)
        self.text_area.bind("<Control-y>", self.do_redo)
        self.text_area.bind("<Control-Y>", self.do_redo)

        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)

        self.header.bind("<Button-1>", self.start_drag)
        self.header.bind("<B1-Motion>", self.do_drag)

        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.do_resize)

    def on_text_select(self, event=None):
        try:
            selected = self.text_area.get("sel.first", "sel.last")
            if selected:
                pyperclip.copy(selected)
        except:
            pass

        self.header.bind("<Button-1>", self.start_drag)
        self.header.bind("<B1-Motion>", self.do_drag)

        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.do_resize)

    def select_all(self, event=None):
        self.text_area.tag_add("sel", "1.0", "end")
        return "break"

    def do_undo(self, event=None):
        try:
            self.text_area.edit_undo()
        except:
            pass
        return "break"

    def do_redo(self, event=None):
        try:
            self.text_area.edit_redo()
        except:
            pass
        return "break"

    def on_opacity_change(self, value):
        self.attributes("-alpha", value / 100)

    def on_text_change(self, event=None):
        if self.save_timer:
            self.after_cancel(self.save_timer)
        self.save_timer = self.after(SAVE_DEBOUNCE_MS, self.save_content)
        self.on_search()

    def on_search(self, event=None):
        search_term = self.search_entry.get().strip()
        self.text_area.tag_remove("search_highlight", "1.0", "end")
        if not search_term:
            return
        content = self.text_area.get("1.0", "end-1c")
        start_index = "1.0"
        while True:
            pos = self.text_area.search(search_term, start_index, stopindex="end")
            if not pos:
                break
            end_pos = f"{pos}+{len(search_term)}c"
            self.text_area.tag_add("search_highlight", pos, end_pos)
            start_index = end_pos
        self.text_area.tag_config("search_highlight", background="#FFFF00", foreground="#000000")

    def save_content(self, event=None):
        content = self.text_area.get("1.0", "end-1c")
        try:
            with open(FILE_PATH, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error saving file: {e}")

    def copy_text(self, event=None):
        content = self.text_area.get("1.0", "end-1c")
        pyperclip.copy(content)
        original_text = self.copy_button.cget("text")
        self.copy_button.configure(text="Copied!")
        self.after(1000, lambda: self.copy_button.configure(text=original_text))

    def format_json(self):
        content = self.text_area.get("1.0", "end-1c").strip()
        if not content:
            return
        try:
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=2)
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", formatted)
        except json.JSONDecodeError:
            pass

    def listify(self):
        content = self.text_area.get("1.0", "end-1c")
        lines = content.split("\n")
        listified = "\n".join(f"- {line}" if line.strip() else "" for line in lines)
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", listified)

    def clean(self):
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Clear Text")
        confirm_window.geometry("280x120")
        confirm_window.resizable(False, False)

        x = self.winfo_x() + (self.winfo_width() // 2) - 140
        y = self.winfo_y() + (self.winfo_height() // 2) - 60
        confirm_window.geometry(f"280x120+{x}+{y}")

        label = ctk.CTkLabel(
            confirm_window,
            text="Are you sure you want to clear all text?",
            font=ctk.CTkFont(size=12)
        )
        label.pack(pady=(20, 20))

        btn_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        def on_yes():
            self.text_area.delete("1.0", "end")
            confirm_window.destroy()

        def on_no():
            confirm_window.destroy()

        yes_btn = ctk.CTkButton(btn_frame, text="Yes", width=80, command=on_yes)
        yes_btn.pack(side="left", padx=10)

        no_btn = ctk.CTkButton(btn_frame, text="No", width=80, fg_color="gray", command=on_no)
        no_btn.pack(side="left", padx=10)

    def toggle_task_mode(self):
        if hasattr(self, 'task_mode') and self.task_mode:
            self.task_mode = False
            content = self.text_area.get("1.0", "end-1c")
            lines = content.split("\n")
            restored = []
            for line in lines:
                if line.startswith("☐ "):
                    restored.append("- " + line[2:])
                elif line.startswith("☑ "):
                    restored.append("- " + line[2:])
                else:
                    restored.append(line)
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", "\n".join(restored))
        else:
            self.task_mode = True
            self.apply_task_mode()

    def apply_task_mode(self):
        content = self.text_area.get("1.0", "end-1c")
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("- "):
                new_lines.append(f"☐ {line[2:]}")
            else:
                new_lines.append(line)
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", "\n".join(new_lines))

    def on_text_click(self, event):
        if not hasattr(self, 'task_mode') or not self.task_mode:
            return
        index = self.text_area.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0])
        line = self.text_area.get(f"{line_num}.0", f"{line_num}.end")
        if line.startswith("☐ "):
            new_line = "☑ " + line[2:]
            self.text_area.delete(f"{line_num}.0", f"{line_num}.end")
            self.text_area.insert(f"{line_num}.0", new_line)
        elif line.startswith("☑ "):
            new_line = "☐ " + line[2:]
            self.text_area.delete(f"{line_num}.0", f"{line_num}.end")
            self.text_area.insert(f"{line_num}.0", new_line)

    def close_app(self):
        self.save_content()
        self.destroy()

    def show_settings(self):
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("250x150")
        settings_window.resizable(False, False)
        settings_window.overrideredirect(True)

        x = self.winfo_x() + (self.winfo_width() // 2) - 125
        y = self.winfo_y() + (self.winfo_height() // 2) - 75
        settings_window.geometry(f"250x150+{x}+{y}")

        close_settings_btn = ctk.CTkButton(
            settings_window,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#c42b2b",
            text_color="#a0a0a0",
            font=ctk.CTkFont(size=14),
            command=settings_window.destroy
        )
        close_settings_btn.place(x=215, y=0)

        startup_label = ctk.CTkLabel(
            settings_window,
            text="Launch on Startup",
            font=ctk.CTkFont(size=12)
        )
        startup_label.place(x=20, y=40)

        self.startup_var = ctk.BooleanVar()
        self.startup_checkbox = ctk.CTkSwitch(
            settings_window,
            text="",
            variable=self.startup_var,
            command=self.toggle_startup
        )
        self.startup_checkbox.place(x=200, y=40)
        self.check_startup_status()

    def check_startup_status(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "FluentNote")
            self.startup_var.set(True)
            winreg.CloseKey(key)
        except:
            self.startup_var.set(False)

    def toggle_startup(self):
        import winreg
        import sys
        import os
        
        app_path = os.path.abspath(sys.argv[0])
        
        try:
            if self.startup_var.get():
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "FluentNote", 0, winreg.REG_SZ, f'"{app_path}"')
                winreg.CloseKey(key)
            else:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
                try:
                    winreg.DeleteValue(key, "FluentNote")
                except:
                    pass
                winreg.CloseKey(key)
        except Exception as e:
            print(f"Startup toggle error: {e}")

    def start_drag(self, event):
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.window_x = self.winfo_x()
        self.window_y = self.winfo_y()

    def do_drag(self, event):
        deltax = event.x_root - self.drag_start_x
        deltay = event.y_root - self.drag_start_y
        x = self.window_x + deltax
        y = self.window_y + deltay
        self.geometry(f"+{x}+{y}")

    def start_resize(self, event):
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.resize_width = self.winfo_width()
        self.resize_height = self.winfo_height()

    def do_resize(self, event):
        deltax = event.x_root - self.resize_start_x
        deltay = event.y_root - self.resize_start_y
        new_width = max(200, self.resize_width + deltax)
        new_height = max(150, self.resize_height + deltay)
        self.geometry(f"{new_width}x{new_height}")


if __name__ == "__main__":
    app = StickyNoteApp()
    app.mainloop()