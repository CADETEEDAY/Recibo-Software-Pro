import os
import sqlite3
import tempfile
import webbrowser
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DatabaseManager:
    def __init__(self, db_name="recibo_software.db"):
        self.db_path = db_name
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("PRAGMA journal_mode=WAL;")
            c.execute("""
                CREATE TABLE IF NOT EXISTS recibos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT NOT NULL,
                    cliente_nome TEXT NOT NULL,
                    cliente_doc TEXT,
                    referente TEXT NOT NULL,
                    valor REAL NOT NULL,
                    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get_proximo_numero(self):
        with self.get_connection() as conn:
            row = conn.execute("SELECT COUNT(id) AS total FROM recibos").fetchone()
            return str((row["total"] if row else 0) + 1)

class ReciboSoftwareApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.title("RECIBO - SOFTWARE v2.8")
        self.geometry("900x600")
        self.minsize(800, 500)
        self.configure(fg_color="#121824")

        header = ctk.CTkFrame(self, height=60, fg_color="#182132", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="RECIBO DIGITAL PRO", font=ctk.CTkFont(size=18, weight="bold"), text_color="#f8fafc").pack(side="left", padx=24)

        container = ctk.CTkFrame(self, fg_color="#1b2438", corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Emissão de Recibos de Pagamento", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3b82f6").pack(pady=(20, 15))

        self.txt_num = self._criar_campo(container, "Número do Documento:", self.db.get_proximo_numero())
        self.txt_cli = self._criar_campo(container, "Nome do Cliente / Pagador:", "")
        self.txt_doc = self._criar_campo(container, "CPF / CNPJ:", "")
        self.txt_val = self._criar_campo(container, "Valor Total (R$):", "0,00")
        self.txt_ref = self._criar_campo(container, "Referente a:", "")

        ctk.CTkButton(
            container, text="Gerar e Imprimir Recibo", height=42, corner_radius=10,
            fg_color="#3b82f6", hover_color="#2563eb", font=ctk.CTkFont(size=13, weight="bold"),
            command=self.gerar_recibo
        ).pack(pady=25)

    def _criar_campo(self, parent, label, valor_inicial):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=40, pady=6)
        ctk.CTkLabel(frame, text=label, width=200, anchor="w", text_color="#8a97ae", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        entry = ctk.CTkEntry(frame, height=36, fg_color="#151c2c", border_color="#2a3752", text_color="#f8fafc")
        entry.insert(0, valor_inicial)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def gerar_recibo(self):
        num = self.txt_num.get().strip()
        cli = self.txt_cli.get().strip()
        doc = self.txt_doc.get().strip()
        val_str = self.txt_val.get().strip()
        ref = self.txt_ref.get().strip()

        if not cli or not val_str:
            messagebox.showwarning("Atenção", "Preencha o Nome do Cliente e o Valor Total.")
            return

        try:
            val_f = float(val_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Valor numérico inválido. Utilize o formato exato, por exemplo: 150,00")
            return

        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO recibos (numero, cliente_nome, cliente_doc, referente, valor) VALUES (?, ?, ?, ?, ?)",
                (num, cli, doc, ref, val_f)
            )
            conn.commit()

        val_formatado = f"{val_f:,.2f}"
        data_atual = datetime.now().strftime('%d/%m/%Y')

        # Montagem do HTML dividida em partes seguras
        html_part1 = "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8'><title>Recibo Nº " + num + "</title>"
        html_part2 = "<style>body { font-family: Arial, sans-serif; padding: 30px; background: #fff; color: #111; }"
        html_part3 = ".recibo { border: 2px solid #333; padding: 25px; max-width: 700px; margin: auto; position: relative; }"
        html_part4 = ".topo { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3b82f6; padding-bottom: 15px; margin-bottom: 20px; }"
        html_part5 = ".titulo { font-size: 24px; font-weight: bold; }.valor-box { font-size: 18px; font-weight: bold; background: #e5e7eb; padding: 5px 15px; }"
        html_part6 = ".campo { margin-bottom: 12px; font-size: 14px; }.linha { border-bottom: 1px solid #000; display: inline-block; width: 75%; font-weight: bold; padding-left: 5px; }"
        html_part7 = ".assinatura { margin-top: 50px; text-align: center; }.traco { border-top: 1px solid #000; width: 300px; margin: auto auto 5px auto; }"
        html_part8 = "@media print { .btn { display: none; } }</style></head><body><div class='recibo'>"
        html_part9 = "<button class='btn' onclick='window.print()' style='padding: 10px 20px; background: #3b82f6; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin-bottom: 15px;'>Imprimir / Salvar PDF</button>"
        html_part10 = "<div class='topo'><div class='titulo'>RECIBO DE PAGAMENTO</div><div class='valor-box'>Nº " + num + " &nbsp;|&nbsp; R$ " + val_formatado + "</div></div>"
        html_part11 = "<div class='campo'><b>Recebi(emos) de:</b> <span class='linha'>" + cli + "</span></div>"
        html_part12 = "<div class='campo'><b>CPF / CNPJ:</b> <span class='linha'>" + doc + "</span></div>"
        html_part13 = "<div class='campo'><b>A quantia de:</b> <span class='linha'>R$ " + val_formatado + "</span></div>"
        html_part14 = "<div class='campo'><b>Referente a:</b> <span class='linha'>" + ref + "</span></div><br>"
        html_part15 = "<p style='text-align: right; font-size: 14px;'>Data: " + data_atual + "</p>"
        html_part16 = "<div class='assinatura'><div class='traco'></div><b>Emitente / Assinatura</b></div></div>"
        html_part17 = "<script>window.print();</script></body></html>"

        html = (
            html_part1 + html_part2 + html_part3 + html_part4 + html_part5 +
            html_part6 + html_part7 + html_part8 + html_part9 + html_part10 +
            html_part11 + html_part12 + html_part13 + html_part14 + html_part15 +
            html_part16 + html_part17
        )

        temp_path = os.path.join(tempfile.gettempdir(), f"recibo_{num}.html")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(html)

        try:
            os.startfile(temp_path)
        except Exception:
            webbrowser.open(temp_path)

        self.txt_num.delete(0, "end")
        self.txt_num.insert(0, self.db.get_proximo_numero())
        messagebox.showinfo("Sucesso", "Recibo gerado com sucesso!")

if __name__ == "__main__":
    app = ReciboSoftwareApp()
    app.mainloop()
