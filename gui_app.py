import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Importe a função que contém a lógica do seu TimeTrackerTransfer
from time_tracker_core import run_time_transfer

# Importe o novo módulo para detectar a versão do Chrome
from chrome_version_detector import get_chrome_version


class TimeTrackerApp:
    def __init__(self, master):
        self.master = master
        master.title("TimeTrackerTransfer GUI")
        master.geometry("500x550")
        master.resizable(False, False)

        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10, "bold"))
        style.configure("TEntry", font=("Arial", 10))
        style.configure("TText", font=("Courier New", 9))
        style.configure("TCheckbutton", background="#f0f0f0")

        # --- Frames para organização ---
        input_frame = ttk.Frame(master, padding="15")
        input_frame.pack(pady=10, padx=10, fill="x")

        # Mover a criação do log_frame e seus widgets para ANTES das chamadas a update_log
        self.log_frame = ttk.Frame(master, padding="15")
        self.log_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Área de Log (Log Frame) ---
        ttk.Label(self.log_frame, text="Log de Atividades:").pack(
            anchor="w", pady=(0, 5))
        self.log_text = tk.Text(
            self.log_frame, wrap="word", height=10, state="disabled")
        self.log_text.pack(fill="both", expand=True)
        self.log_scrollbar = ttk.Scrollbar(
            self.log_frame, command=self.log_text.yview)
        self.log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)

        # --- Agora as chamadas a update_log podem ser feitas com segurança ---
        # Elas estavam aqui antes de self.log_text ser definido
        detected_chrome_version = get_chrome_version()
        if detected_chrome_version:
            self.create_input_field(input_frame, "Versão ChromeDriver:",
                                    "chromedriver_version_entry", default_value=detected_chrome_version)
            self.update_log(
                f"Versão do Chrome detectada automaticamente: {detected_chrome_version}")
        else:
            self.create_input_field(input_frame, "Versão ChromeDriver (Manual):",
                                    "chromedriver_version_entry", default_value="N/A - Insira manualmente")
            self.update_log(
                "AVISO: Não foi possível detectar a versão do Chrome automaticamente. Por favor, insira manualmente.")
            self.update_log(
                "Abra o Chrome > Mais opções (3 pontos) > Ajuda > Sobre o Google Chrome.")

        # --- Campos de Entrada (Input Frame) --- (já estavam aqui)
        self.create_input_field(
            input_frame, "Usuário NetProject:", "netproject_user_entry")
        self.create_password_field(
            input_frame, "Senha NetProject:", "netproject_password_entry")

        self.create_input_field(input_frame, "Usuário SGI:", "sgi_user_entry")
        self.create_password_field(
            input_frame, "Senha SGI:", "sgi_password_entry")

        button_frame = ttk.Frame(master, padding="10")
        button_frame.pack(pady=5, padx=10, fill="x")

        # --- Botão de Execução (Button Frame) --- (já estavam aqui)
        self.run_button = ttk.Button(
            button_frame, text="Iniciar Transferência", command=self.start_transfer_thread)
        self.run_button.pack(side="right", padx=5)

        self.clear_button = ttk.Button(
            button_frame, text="Limpar Log", command=self.clear_log)
        self.clear_button.pack(side="left", padx=5)

    def create_input_field(self, parent_frame, label_text, entry_attr_name, default_value=""):
        frame = ttk.Frame(parent_frame)
        frame.pack(pady=5, fill="x")
        label = ttk.Label(frame, text=label_text, width=20)
        label.pack(side="left", padx=(0, 10))
        entry = ttk.Entry(frame)
        entry.pack(side="left", fill="x", expand=True)
        setattr(self, entry_attr_name, entry)
        if default_value:
            entry.insert(0, default_value)
            # Rola para o final do texto se for muito longo (útil para versões)
            entry.xview_moveto(1)

    def create_password_field(self, parent_frame, label_text, entry_attr_name):
        frame = ttk.Frame(parent_frame)
        frame.pack(pady=5, fill="x")
        label = ttk.Label(frame, text=label_text, width=20)
        label.pack(side="left", padx=(0, 10))
        entry = ttk.Entry(frame, show="*")
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        setattr(self, entry_attr_name, entry)
        show_password_var = tk.BooleanVar(value=False)
        def toggle_func(e=entry): return self.toggle_password_visibility(
            e, show_password_var)
        check_button = ttk.Checkbutton(frame, text="Exibir",
                                       variable=show_password_var,
                                       command=toggle_func)
        check_button.pack(side="left")

    def toggle_password_visibility(self, entry_widget, show_password_var):
        if show_password_var.get():
            entry_widget.config(show="")
        else:
            entry_widget.config(show="*")

    def update_log(self, message):
        # Esta função agora tem certeza que self.log_text já existe
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

    def start_transfer_thread(self):
        netproject_user = self.netproject_user_entry.get()
        netproject_password = self.netproject_password_entry.get()
        sgi_user = self.sgi_user_entry.get()
        sgi_password = self.sgi_password_entry.get()
        chromedriver_version = self.chromedriver_version_entry.get()

        if not all([netproject_user, netproject_password, sgi_user, sgi_password, chromedriver_version]):
            messagebox.showerror(
                "Erro", "Por favor, preencha todos os campos.")
            return

        if "N/A - Insira manualmente" in chromedriver_version or not chromedriver_version.strip():
            messagebox.showwarning(
                "Aviso", "A versão do Chrome/ChromeDriver não foi detectada automaticamente. Por favor, insira-a manualmente no campo 'Versão ChromeDriver' ou corrija a instalação do Chrome.")
            return

        self.update_log("Iniciando processo de transferência...")
        self.run_button.config(state="disabled")

        transfer_thread = threading.Thread(
            target=run_time_transfer,
            args=(
                netproject_user,
                netproject_password,
                sgi_user,
                sgi_password,
                chromedriver_version,
                self.update_log
            )
        )
        transfer_thread.start()

        self.master.after(100, self.check_transfer_thread, transfer_thread)

    def check_transfer_thread(self, thread):
        if thread.is_alive():
            self.master.after(100, self.check_transfer_thread, thread)
        else:
            self.run_button.config(state="normal")
            self.update_log(
                "Processo concluído ou finalizado. Verifique o log acima.")


# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.mainloop()
