import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import requests
import base64
import os

# ============== CONFIG =================
GITHUB_TOKEN = "PON_AQUI_TU_TOKEN_NUEVO"
OWNER = "xXKuroiKenshiXx"
REPO = "MIDI-hytale"
BRANCH = "main"
# ======================================

API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

class GitHubMIDManager(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()
        self.title("GitHub MID Manager")
        self.geometry("900x500")

        self.dropped_file = None

        self.create_ui()
        self.load_mid_files()

    def create_ui(self):
        self.tree = ttk.Treeview(
            self,
            columns=("nombre", "copiar", "renombrar"),
            show="headings"
        )

        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("copiar", text="Copiar URL")
        self.tree.heading("renombrar", text="Cambiar nombre")

        self.tree.column("nombre", width=450)
        self.tree.column("copiar", width=150, anchor="center")
        self.tree.column("renombrar", width=150, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Button-1>", self.on_click)

        self.drop_label = tk.Label(
            self,
            text="ARRASTRA UN ARCHIVO .MID AQUÍ",
            bg="#333",
            fg="white",
            height=3
        )
        self.drop_label.pack(fill=tk.X, padx=10)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)

        tk.Button(self, text="SUBIR", command=self.upload_file).pack(pady=10)

    # --------- GITHUB ----------
    def load_mid_files(self):
        self.tree.delete(*self.tree.get_children())

        r = requests.get(API_URL, headers=HEADERS)
        if r.status_code != 200:
            messagebox.showerror("Error", f"GitHub error: {r.status_code}")
            return

        for f in r.json():
            if f["name"].lower().endswith(".mid"):
                self.tree.insert("", tk.END, values=(f["name"], "Copiar", "Cambiar"))

    def copy_raw_url(self, filename):
        url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{filename}"
        self.clipboard_clear()
        self.clipboard_append(url)
        messagebox.showinfo("Copiado", "URL RAW copiada")

    def rename_file(self, filename):
        new_name = simpledialog.askstring("Renombrar", "Nuevo nombre (.mid):")
        if not new_name or not new_name.endswith(".mid"):
            return

        file_url = f"{API_URL}/{filename}"
        r = requests.get(file_url, headers=HEADERS)
        if r.status_code != 200:
            messagebox.showerror("Error", "No se pudo obtener el archivo")
            return

        sha = r.json()["sha"]
        content = r.json()["content"]

        put = requests.put(
            f"{API_URL}/{new_name}",
            headers=HEADERS,
            json={
                "message": f"Rename {filename} to {new_name}",
                "content": content,
                "branch": BRANCH
            }
        )

        if put.status_code not in (200, 201):
            messagebox.showerror("Error", "No se pudo renombrar")
            return

        requests.delete(
            file_url,
            headers=HEADERS,
            json={
                "message": f"Delete {filename}",
                "sha": sha,
                "branch": BRANCH
            }
        )

        self.load_mid_files()

    # -------- EVENTS ----------
    def on_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item:
            return

        filename = self.tree.item(item, "values")[0]

        if col == "#2":
            self.copy_raw_url(filename)
        elif col == "#3":
            self.rename_file(filename)

    def on_drop(self, event):
        self.dropped_file = self.tk.splitlist(event.data)[0]
        self.drop_label.config(
            text=f"Archivo seleccionado: {os.path.basename(self.dropped_file)}"
        )

    def upload_file(self):
        if not self.dropped_file:
            messagebox.showerror("Error", "No hay archivo seleccionado")
            return

        new_name = simpledialog.askstring("Nombre", "Nombre del archivo (.mid):")
        if not new_name or not new_name.endswith(".mid"):
            return

        with open(self.dropped_file, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        r = requests.put(
            f"{API_URL}/{new_name}",
            headers=HEADERS,
            json={
                "message": f"Upload {new_name}",
                "content": content,
                "branch": BRANCH
            }
        )

        if r.status_code in (200, 201):
            messagebox.showinfo("Éxito", "Archivo subido")
            self.load_mid_files()
        else:
            messagebox.showerror("Error", f"GitHub error {r.status_code}")

if __name__ == "__main__":
    GitHubMIDManager().mainloop()
