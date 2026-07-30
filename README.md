#  CryptoJournal

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-@moscow_professor-26A5E4?logo=telegram&logoColor=white)](https://t.me/moscow_professor)

**CryptoJournal** is a secure, encrypted diary application built with Python and `customtkinter`.  
It allows you to write, format, and encrypt your personal notes with military‑grade AES encryption (Fernet).  
Your data is stored in a single `.crypt` file – only you can read it with your secret key.


##  Features

- 🔑 **Strong encryption** – each record is encrypted with a Fernet (AES‑128‑CBC) key.
- 📝 **Rich text formatting** – bold, italic, and background highlighting.
- 📚 **Organized records** – each entry has a title, timestamp, and collapsible preview.
- 🔍 **Spell checking** – optional support for English and Russian (requires `pyspellchecker`).
- 🖱️ **Clipboard support** – copy/paste/cut with keyboard shortcuts and right‑click menu.
- 📁 **Single‑file storage** – all encrypted records are stored in a `.crypt` file.

---

##  Installation

### 1. Clone the repository
```bash
git clone https://github.com/moscow-professor-codehub/CryptoJournal.git
cd crypto-journal
```

### 2. Install dependencies
Create a virtual environment and install required packages:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**`requirements.txt`**:
```
customtkinter>=5.2.0
cryptography>=41.0.0
pyspellchecker>=0.7.0  # optional, for spell checking
```

### 3. Run the application
```bash
python main.py
```

---

##  Usage

1. **Open or create a journal** – click the `Files` button (top‑left) or use `New Journal`.
2. **Enter your encryption key** – you can generate a new key with the `New Key` button. **Keep it safe!** Without it, your data cannot be recovered.
3. **Write a new entry** – fill in the title and the text body. Use the toolbar to apply formatting.
4. **Encrypt** – click `Encrypt` to append the current record to the journal file.
5. **Decrypt** – click `Decrypt` to see all records. Each record is shown as a card; double‑click a card to load it into the editor.
6. **Spell checking** – misspelled words are highlighted in red (automatic on space/return, or use the context menu to check all).

---

## ⚙️ Command‑line Arguments

None – the application runs with a graphical interface only.

---

##  File Format

The journal is stored as a plain text file where each line is an encrypted JSON object (Base64‑encoded).  
Example of a decrypted record:
```json
{
  "title": "My first entry",
  "date": "2026-07-30 14:23",
  "content": "Hello, world!",
  "tags": {"bold": [[0,5]]}
}
```

---

##  License and Attribution

This project is distributed under the **MIT License**.  
When you use or distribute this code, you **must** retain the original copyright notice and mention the author.

> **Author**: [@moscow_professor](https://t.me/moscow_professor)

For the full license text, see the [`LICENSE`](LICENSE) file.

---

##  Connect with the author

- Telegram: [t.me/moscow_professor](https://t.me/moscow_professor)

---

If you have any issues or suggestions, feel free to open an **Issue** on GitHub.  
Happy journaling! 📖
