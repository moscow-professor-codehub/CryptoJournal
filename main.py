#####################################################################
#       Developed by @moscow_professor                              # 
#       t.me/moscow_professor                                       #
#       If you publish or use my code,                              #
#       please at least leave a link to my profile in Telegram.     #
#####################################################################

#!/usr/bin/env python3

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import os
import json
import re
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional, Dict, Any

# ---------- Spell checker (optional) ----------
try:
    from spellchecker import SpellChecker
    spell_en = SpellChecker(language='en')
    try:
        spell_ru = SpellChecker(language='ru')
    except Exception:
        spell_ru = None
except ImportError:
    spell_en = None
    spell_ru = None

# ---------- Global state ----------
full_file_path = "Journal.crypt"
display_name_var: Optional[ctk.StringVar] = None

# ---------- UI constants ----------
BORDER_COLOR = "#FFFFFF"
BG_COLOR = '#2e2e2e'
BTN_STYLE = {
    "fg_color": "#000000",
    "hover_color": "#575757",
    "border_color": BORDER_COLOR,
    "text_color": "white",
    "height": 30,
    "corner_radius": 25
}


# ---------- Clipboard helpers ----------
def enable_clipboard_support(widget):
    """Add paste/copy/cut with keyboard shortcuts and context menu."""
    def paste(event=None):
        try:
            text = app.clipboard_get()
            if isinstance(widget, ctk.CTkEntry):
                if widget.select_present():
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", text)
            elif isinstance(widget, ctk.CTkTextbox):
                if widget.tag_ranges("sel"):
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", text)
            elif isinstance(widget, tk.Entry):
                if widget.selection_present():
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", text)
            elif isinstance(widget, tk.Text):
                if widget.tag_ranges("sel"):
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", text)
        except:
            pass

    def copy(event=None):
        try:
            if isinstance(widget, ctk.CTkEntry):
                if widget.select_present():
                    text = widget.selection_get()
                    app.clipboard_clear()
                    app.clipboard_append(text)
            elif isinstance(widget, ctk.CTkTextbox):
                if widget.tag_ranges("sel"):
                    text = widget.get("sel.first", "sel.last")
                    app.clipboard_clear()
                    app.clipboard_append(text)
            elif isinstance(widget, tk.Entry):
                if widget.selection_present():
                    text = widget.selection_get()
                    app.clipboard_clear()
                    app.clipboard_append(text)
            elif isinstance(widget, tk.Text):
                if widget.tag_ranges("sel"):
                    text = widget.get("sel.first", "sel.last")
                    app.clipboard_clear()
                    app.clipboard_append(text)
        except:
            pass

    def cut(event=None):
        copy()
        if isinstance(widget, ctk.CTkEntry):
            widget.delete("sel.first", "sel.last")
        elif isinstance(widget, ctk.CTkTextbox):
            widget.delete("sel.first", "sel.last")
        elif isinstance(widget, tk.Entry):
            widget.delete("sel.first", "sel.last")
        elif isinstance(widget, tk.Text):
            widget.delete("sel.first", "sel.last")

    def context_menu(event):
        m = tk.Menu(widget, tearoff=0)
        m.add_command(label="Paste", command=paste)
        m.add_command(label="Copy", command=copy)
        m.add_command(label="Cut", command=cut)
        m.tk_popup(event.x_root, event.y_root)

    widget.bind("<Control-v>", paste)
    widget.bind("<Control-V>", paste)
    widget.bind("<Control-c>", copy)
    widget.bind("<Control-C>", copy)
    widget.bind("<Control-x>", cut)
    widget.bind("<Control-X>", cut)
    widget.bind("<Command-v>", paste)
    widget.bind("<Command-c>", copy)
    widget.bind("<Command-x>", cut)
    widget.bind("<Button-3>", context_menu)


# ---------- Formatting helpers ----------
def clear_formatting_tags(txt):
    """Remove all user‑applied formatting tags except selection and misspelled."""
    for tag in txt.tag_names():
        if tag not in ("sel", "misspelled"):
            txt.tag_remove(tag, "1.0", tk.END)


def extract_formatting(txt):
    """
    Return (plain_text, tags_dict) where tags_dict maps tag_name
    to a list of [start_char, end_char] positions.
    """
    content = txt.get("1.0", "end-1c")
    tags = {}
    for tag in txt.tag_names():
        if tag in ("sel", "misspelled"):
            continue
        ranges = txt.tag_ranges(tag)
        if not ranges:
            continue
        positions = []
        for i in range(0, len(ranges), 2):
            s = ranges[i]
            e = ranges[i + 1]
            s_char = txt.count("1.0", s, "chars")[0]
            e_char = txt.count("1.0", e, "chars")[0]
            if s_char <= len(content) and e_char <= len(content):
                positions.append([s_char, e_char])
        if positions:
            tags[tag] = positions
    return content, tags


def apply_formatting(txt, content, tags):
    """Restore formatting from saved tags."""
    txt.delete("1.0", "end")
    txt.insert("1.0", content)
    clear_formatting_tags(txt)
    for tag, positions in tags.items():
        if tag.startswith("bg_"):
            txt.tag_config(tag, background=tag[3:])
        elif tag == "bold":
            txt.tag_config(tag, font=("DejaVu Sans Mono", 18, "bold"))
        elif tag == "italic":
            txt.tag_config(tag, font=("DejaVu Sans Mono", 18, "italic"))
        for s_char, e_char in positions:
            s_idx = txt.index(f"1.0+{s_char}c")
            e_idx = txt.index(f"1.0+{e_char}c")
            txt.tag_add(tag, s_idx, e_idx)


# ---------- Main actions ----------
def new_journal():
    global full_file_path
    path = filedialog.asksaveasfilename(
        defaultextension=".crypt",
        filetypes=[("Encrypted files", "*.crypt"), ("All files", "*.*")]
    )
    if not path:
        return
    with open(path, 'wb') as f:
        pass
    full_file_path = path
    display_name_var.set(os.path.basename(path))
    for w in records_scroll_frame.winfo_children():
        w.destroy()
    title_entry.delete(0, "end")
    text_input_box.delete("1.0", "end")
    key_entry.delete(0, "end")
    messagebox.showinfo("Success", f"New journal created: {os.path.basename(path)}")


def encrypt_record():
    key_str = key_entry.get().strip()
    if not key_str:
        messagebox.showerror("Error", "Enter encryption key")
        return
    try:
        fernet = Fernet(key_str.encode())
    except Exception as e:
        messagebox.showerror("Key error", f"Invalid key format:\n{e}")
        return

    title = title_entry.get().strip()
    if not title:
        messagebox.showwarning("Warning", "Please enter a title")
        return

    content, tags = extract_formatting(text_input_box)
    if not content.strip():
        messagebox.showwarning("Warning", "Text is empty")
        return

    record = {
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": content,
        "tags": tags
    }
    try:
        encrypted = fernet.encrypt(json.dumps(record, ensure_ascii=False).encode())
    except Exception as e:
        messagebox.showerror("Encryption error", str(e))
        return

    try:
        with open(full_file_path, 'ab') as f:
            f.write(encrypted + b'\n')
        messagebox.showinfo("Success", "Record encrypted and appended")
        title_entry.delete(0, "end")
        text_input_box.delete("1.0", "end")
    except Exception as e:
        messagebox.showerror("Write error", str(e))


def build_record_card(parent, record):
    """Create a collapsible card for a decrypted record."""
    title = record['title']
    date = record['date']
    content = record['content']

    card = ctk.CTkFrame(parent, fg_color="#000000", corner_radius=10)
    card.pack(fill="x", padx=5, pady=5)

    header = ctk.CTkFrame(card, fg_color="transparent")
    header.pack(fill="x", padx=10, pady=(10, 5))

    info = ctk.CTkFrame(header, fg_color="transparent", border_color="white")
    info.pack(side="left", fill="x", expand=True)

    t_lbl = ctk.CTkLabel(
        info, text=title, font=("Arial", 14, "bold"),
        text_color="white", anchor="w"
    )
    t_lbl.pack(anchor="w", fill="x")

    d_lbl = ctk.CTkLabel(
        info, text=date, font=("Arial", 10),
        text_color="#FFFFFF", anchor="w"
    )
    d_lbl.pack(anchor="w")

    expand_state = {"expanded": False}
    content_frame = ctk.CTkFrame(card, fg_color="transparent", border_color="white")
    content_label = ctk.CTkLabel(
        content_frame, text=content, wraplength=800,
        justify="left", anchor="w", text_color="#FFFFFF",
        font=("Arial", 12)
    )
    content_label.pack(fill="x", padx=10, pady=5)

    def update_wraplength(event):
        if event.width > 10:
            content_label.configure(wraplength=event.width - 20)
    content_frame.bind("<Configure>", update_wraplength)

    toggle_btn = ctk.CTkButton(
        header, text="▼", width=30, height=30, corner_radius=15,
        fg_color="transparent", hover_color="#777777",
        text_color="#FFFFFF", border_color="white", border_width=1
    )
    toggle_btn.pack(side="right", anchor="ne")

    def toggle():
        if expand_state["expanded"]:
            content_frame.pack_forget()
            toggle_btn.configure(text="▼")
            expand_state["expanded"] = False
        else:
            content_frame.pack(fill="x", padx=10, pady=(0, 10))
            toggle_btn.configure(text="▲")
            expand_state["expanded"] = True
    toggle_btn.configure(command=toggle)

    def on_double_click(event):
        title_entry.delete(0, "end")
        title_entry.insert(0, record['title'])
        apply_formatting(text_input_box, record.get('content', ''), record.get('tags', {}))

    card.bind("<Double-1>", on_double_click)
    t_lbl.bind("<Double-1>", on_double_click)
    d_lbl.bind("<Double-1>", on_double_click)


def decrypt_all():
    key_str = key_entry.get().strip()
    if not key_str:
        messagebox.showerror("Error", "Enter encryption key")
        return
    try:
        fernet = Fernet(key_str.encode())
    except Exception as e:
        messagebox.showerror("Key error", f"Invalid key format:\n{e}")
        return

    if not os.path.isfile(full_file_path):
        messagebox.showerror("Error", "File not found")
        return

    try:
        with open(full_file_path, 'rb') as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
    except Exception as e:
        messagebox.showerror("Read error", str(e))
        return

    if not lines:
        messagebox.showinfo("Info", "File contains no encrypted data")
        return

    for w in records_scroll_frame.winfo_children():
        w.destroy()

    for idx, enc in enumerate(lines, 1):
        try:
            plain = fernet.decrypt(enc).decode()
            build_record_card(records_scroll_frame, json.loads(plain))
        except InvalidToken:
            build_record_card(records_scroll_frame, {
                "title": f"Record #{idx} [Invalid Key]",
                "date": "",
                "content": "Cannot decrypt, invalid key."
            })
        except Exception as e:
            build_record_card(records_scroll_frame, {
                "title": f"Record #{idx} [Error]",
                "date": "",
                "content": str(e)
            })

    messagebox.showinfo("Done", f"Decrypted {len(lines)} records")


def generate_key():
    key = Fernet.generate_key()
    key_str = key.decode()
    key_entry.delete(0, "end")
    key_entry.insert(0, key_str)

    dialog = ctk.CTkToplevel(app)
    dialog.title("New Key")
    dialog.geometry("500x200")
    dialog.resizable(False, False)
    ctk.CTkLabel(
        dialog, text="Your new secret key:", font=("Arial", 14, "bold")
    ).pack(pady=20)

    key_display = ctk.CTkEntry(dialog, width=400, justify="center")
    key_display.insert(0, key_str)
    key_display.configure(state="readonly")
    key_display.pack(pady=5)

    ctk.CTkLabel(
        dialog,
        text="Save it! Without the key the data cannot be recovered.",
        text_color="red"
    ).pack(pady=10)

    def copy_to_clipboard():
        dialog.clipboard_clear()
        dialog.clipboard_append(key_str)
        messagebox.showinfo("Copied", "Key copied to clipboard")
    ctk.CTkButton(dialog, text="Copy", command=copy_to_clipboard).pack(pady=5)


def choose_file():
    global full_file_path
    path = filedialog.askopenfilename(
        defaultextension=".crypt",
        filetypes=[("Encrypted files", "*.crypt"), ("All files", "*.*")]
    )
    if path:
        full_file_path = path
        display_name_var.set(os.path.basename(path))
        for w in records_scroll_frame.winfo_children():
            w.destroy()


# ---------- Spell check ----------
def auto_check_spelling(event=None):
    if not spell_en:
        return

    cursor = text_input_box.index("insert")
    before = text_input_box.get("1.0", cursor)
    words = re.findall(r'\b\w+\b', before)
    if not words:
        return

    last_word = words[-1]
    start = text_input_box.search(last_word, cursor, backwards=True, regexp=False)
    if not start:
        return
    end = f"{start}+{len(last_word)}c"

    if text_input_box.get(end, f"{end}+1c") not in (" ", "\n", "\r", "\t", ""):
        return

    text_input_box.tag_remove("misspelled", start, end)
    if last_word.isdigit():
        return

    wrong = False
    if re.search(r'[а-яА-Я]', last_word):
        if spell_ru and spell_ru.unknown([last_word]):
            wrong = True
    else:
        if spell_en.unknown([last_word.lower()]):
            wrong = True

    if wrong:
        text_input_box.tag_add("misspelled", start, end)


def check_all_spelling():
    if not spell_en:
        messagebox.showerror("Error", "pyspellchecker not installed.")
        return

    content = text_input_box.get("1.0", "end-1c")
    if not content.strip():
        messagebox.showinfo("Spell Check", "No text to check")
        return

    text_input_box.tag_delete("misspelled")
    text_input_box.tag_config("misspelled", foreground="red")

    words = re.findall(r'\b\w+\b', content)
    wrong = set()
    for w in words:
        if w.isdigit():
            continue
        if re.search(r'[а-яА-Я]', w):
            if spell_ru and spell_ru.unknown([w]):
                wrong.add(w)
        else:
            if spell_en.unknown([w.lower()]):
                wrong.add(w)

    for w in wrong:
        pos = "1.0"
        while True:
            p = text_input_box.search(w, pos, tk.END)
            if not p:
                break
            e = f"{p}+{len(w)}c"
            text_input_box.tag_add("misspelled", p, e)
            pos = e

    if wrong:
        messagebox.showinfo("Spell Check", f"Possible errors: {', '.join(sorted(wrong))}")
    else:
        messagebox.showinfo("Spell Check", "No errors found")


# ---------- Formatting buttons ----------
def apply_format(tag):
    try:
        if text_input_box.tag_ranges("sel"):
            s = text_input_box.index("sel.first")
            e = text_input_box.index("sel.last")
            if tag in text_input_box.tag_names(s):
                text_input_box.tag_remove(tag, s, e)
            else:
                text_input_box.tag_add(tag, s, e)
    except:
        pass


def apply_background_color():
    try:
        if not text_input_box.tag_ranges("sel"):
            messagebox.showinfo("Info", "Select text to highlight")
            return
        color = colorchooser.askcolor(title="Pick background color")[1]
        if color:
            s = text_input_box.index("sel.first")
            e = text_input_box.index("sel.last")
            for tag in text_input_box.tag_names(s):
                if tag.startswith("bg_"):
                    text_input_box.tag_remove(tag, s, e)
            tag = f"bg_{color}"
            text_input_box.tag_config(tag, background=color)
            text_input_box.tag_add(tag, s, e)
    except:
        pass


# ---------- Application UI ----------
app = ctk.CTk()
app.title("CryptoJournal")
app.geometry("1500x1080")
app.minsize(1200, 800)
app.configure(fg_color="#242424")

display_name_var = ctk.StringVar(value=os.path.basename(full_file_path))

# Top bar
top_frame = ctk.CTkFrame(
    app, border_color=BORDER_COLOR, border_width=3,
    fg_color=BG_COLOR, height=60, corner_radius=25
)
top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
top_frame.grid_columnconfigure(0, weight=0)
top_frame.grid_columnconfigure(1, weight=0)
top_frame.grid_columnconfigure(2, weight=1)

select_btn = ctk.CTkButton(
    top_frame, fg_color='#000000', hover_color="#575757",
    border_color=BORDER_COLOR, text="Files", height=30, width=30,
    corner_radius=30, command=choose_file
)
select_btn.grid(row=0, column=0, padx=(10, 5), pady=10)

filename_label = ctk.CTkLabel(
    top_frame, textvariable=display_name_var,
    text_color="white", font=("Monospace", 14, "bold"),
    width=200, anchor="w"
)
filename_label.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="w")

key_entry = ctk.CTkEntry(
    top_frame, width=400, fg_color="#828282",
    border_color=BORDER_COLOR, border_width=1,
    corner_radius=20, text_color='white'
)
key_entry.grid(row=0, column=2, padx=10, pady=10, sticky="e")

# Action panel
action_frame = ctk.CTkFrame(
    app, border_color=BORDER_COLOR, border_width=3,
    fg_color=BG_COLOR, height=50, corner_radius=25
)
action_frame.grid(row=0, column=1, padx=0, pady=(20, 10), sticky="ew")

btn_new = ctk.CTkButton(
    action_frame, text="New Journal", width=130,
    **BTN_STYLE, command=new_journal
)
btn_new.grid(row=0, column=0, padx=5, pady=10)

btn_encrypt = ctk.CTkButton(
    action_frame, text="Encrypt", width=130,
    **BTN_STYLE, command=encrypt_record
)
btn_encrypt.grid(row=0, column=1, padx=5, pady=10)

btn_decrypt = ctk.CTkButton(
    action_frame, text="Decrypt", width=130,
    **BTN_STYLE, command=decrypt_all
)
btn_decrypt.grid(row=0, column=2, padx=5, pady=10)

btn_key = ctk.CTkButton(
    action_frame, text="New Key", width=130,
    **BTN_STYLE, command=generate_key
)
btn_key.grid(row=0, column=3, padx=5, pady=10)

for i in range(4):
    action_frame.grid_columnconfigure(i, weight=1)

# Left panel (record list)
left_frame = ctk.CTkFrame(
    app, border_color=BORDER_COLOR, border_width=3,
    fg_color=BG_COLOR, corner_radius=25
)
left_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
left_frame.grid_rowconfigure(0, weight=1)
left_frame.grid_columnconfigure(0, weight=1)

records_scroll_frame = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
records_scroll_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Right panel (editor)
right_frame = ctk.CTkFrame(
    app, border_color=BORDER_COLOR, border_width=3,
    fg_color=BG_COLOR, corner_radius=25
)
right_frame.grid(row=2, column=1, padx=(0, 20), pady=(0, 20), sticky="nsew")
right_frame.grid_rowconfigure(1, weight=1)
right_frame.grid_columnconfigure(0, weight=1)

title_entry = ctk.CTkEntry(
    right_frame, placeholder_text="Enter title...",
    fg_color=BG_COLOR, border_color=BORDER_COLOR,
    text_color="white", corner_radius=15, border_width=2,
    font=("Arial", 14)
)
title_entry.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")

text_container = ctk.CTkFrame(right_frame, fg_color="transparent")
text_container.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
text_container.grid_rowconfigure(0, weight=1)
text_container.grid_columnconfigure(0, weight=1)

text_input_box = tk.Text(
    text_container, wrap="word", bg=BG_COLOR, fg="white",
    font=("DejaVu Sans Mono", 18, "bold"), borderwidth=0,
    highlightthickness=0, insertbackground="white", padx=10
)
text_input_box.grid(row=0, column=0, sticky="nsew", pady=(0, 70))

scrollbar = ctk.CTkScrollbar(text_container, command=text_input_box.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
text_input_box.configure(yscrollcommand=scrollbar.set)

# Bottom toolbar
toolbar_frame = ctk.CTkFrame(text_container, fg_color="#3a3a3a", corner_radius=12, height=45)
toolbar_frame.place(relx=0.5, rely=1.0, anchor="s", relwidth=0.95, y=-10)
toolbar_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

btn_bold = ctk.CTkButton(
    toolbar_frame, text="Bold", width=30, height=30, corner_radius=15,
    fg_color="#555555", hover_color="#777777", text_color="white",
    command=lambda: apply_format("bold")
)
btn_bold.grid(row=0, column=0, padx=5, pady=5)

btn_italic = ctk.CTkButton(
    toolbar_frame, text="Italic", width=30, height=30, corner_radius=15,
    fg_color="#555555", hover_color="#777777", text_color="white",
    command=lambda: apply_format("italic")
)
btn_italic.grid(row=0, column=1, padx=5, pady=5)

btn_bg = ctk.CTkButton(
    toolbar_frame, text="Marker", width=30, height=30, corner_radius=15,
    fg_color="#555555", hover_color="#777777", text_color="white",
    command=apply_background_color
)
btn_bg.grid(row=0, column=2, padx=5, pady=0)

btn_clear = ctk.CTkButton(
    toolbar_frame, text="Clear", width=30, height=30, corner_radius=15,
    fg_color="#555555", hover_color="#777777", text_color="white",
    command=lambda: (
        text_input_box.tag_remove("bold", "1.0", tk.END),
        text_input_box.tag_remove("italic", "1.0", tk.END),
        [text_input_box.tag_remove(tag, "1.0", tk.END)
         for tag in text_input_box.tag_names() if tag.startswith("bg_")]
    )
)
btn_clear.grid(row=0, column=3, padx=5, pady=5)

# Configure text tags
text_input_box.tag_config("bold", font=("DejaVu Sans Mono", 18, "bold"))
text_input_box.tag_config("italic", font=("DejaVu Sans Mono", 18, "italic"))
text_input_box.tag_config("misspelled", foreground="red")

# Layout
app.grid_rowconfigure(2, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=3)

# Enable clipboard and spellcheck bindings
enable_clipboard_support(key_entry)
enable_clipboard_support(title_entry)
enable_clipboard_support(text_input_box)

text_input_box.bind("<space>", auto_check_spelling)
text_input_box.bind("<Return>", auto_check_spelling)

app.mainloop()
