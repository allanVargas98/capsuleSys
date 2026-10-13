import tkinter as ttk
import customtkinter as ctk
import os 
import pandas as pd

def validar_login():
    usuario = user_entry.get()
    senha = senha_entry.get()
    
    if usuario == "admin" and senha == "1234":
        resultado_label.configure(text="Login realizado com sucesso!", text_color="green")
        
        tela_principal = ctk.CTkToplevel(app)
        tela_principal.geometry("400x300")
        tela_principal.title("Tela Principal")
        tela_principal.lift()
        tela_principal.focus_force()
        tela_principal.grab_set()
        
        menu = ctk.CTkOptionMenu(tela_principal)
        msg = ctk.CTkLabel(tela_principal, text=f"Bem-vindo, {usuario}!")
        msg.pack(pady=20)
        botao_sair = ctk.CTkButton(tela_principal, text="Sair", command=tela_principal.destroy)
        botao_sair.pack(pady=10)
        app.withdraw() #Fecha a tela de login quando user logar na sessão 


        
    else:
        resultado_label.configure(text="Usuário ou senha inválidos.", text_color="red")


app = ctk.CTk()
app.geometry("300x300")
app.title("RH MULLER")
user = ctk.CTkLabel(app,text="Usuário")
user.pack(pady=5)
user_entry = ctk.CTkEntry(app,placeholder_text="Informe seu Usuário")
user_entry.pack(pady=5)
senha = ctk.CTkLabel(app,text="Senha")
senha.pack(pady=5)
senha_entry=ctk.CTkEntry(app,placeholder_text="Informe sua Senha", show="*")
senha_entry.pack(pady=5)
login = ctk.CTkButton(app, text="login", command=validar_login)
login.pack(pady=5)
resultado_label = ctk.CTkLabel(app, text="")
resultado_label.pack(pady=10)



app.mainloop()