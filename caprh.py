import streamlit as st
import pandas as pd
import os

st.title("RH")

def tela_login():
    st.title("Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if os.path.exists("usuarios.csv"):
            df_usuarios = pd.read_csv("usuarios.csv")
            if ((df_usuarios["Usuario"] == usuario) & (df_usuarios["Senha"] == senha)).any():
                st.success("Login realizado com sucesso!")
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario  # guarda quem entrou
            else:
                st.error("Usuário ou senha inválidos.")
        else:
            if usuario == "admin" and senha == "1234":
                st.success("Login realizado com sucesso!")
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
            else:
                st.error("Usuário ou senha inválidos.")

# Inicializa o estado se ainda não existir
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# Controle de login
if not st.session_state["logado"]:
    tela_login()
else:
    menu = st.sidebar.radio("Selecione uma área", ["Cadastros", "Folha de Pagamento", "Benefícios", "Recrutamento", "Treinamento", "Desempenho", "Relatórios"]
)

match menu:
    case "Cadastros":
        st.header("Cadastros")
        cadastro_opcao = st.radio("Escolha uma Opção:", ["Cadastro de Funcionário", "Cadastro de Funções", "Cadastro de Candidatura"], horizontal=True)
        match cadastro_opcao:
            case "Cadastro de Funcionário":
                nome = st.text_input("Nome Completo")
                cpf = st.text_input("CPF")
                funcao = st.text_input("Função")
                salario = st.number_input("Salário")
                filial = st.text_input("Filial")
                if st.button ("Salvar"):
                    novo_funcionario = pd.DataFrame([{"Nome Completo":nome, "cpf":cpf, "Funçao":funcao,  "Salário":salario, "Filial":filial}])
                    if os.path.exists("funcionario.csv"):
                        novo_funcionario.to_csv("funcionario.csv", mode="a", header=False, index=False)
                    else:
                        novo_funcionario.to_csv("funcionario.csv", index=False)
                    st.success(f"Funcionário Cadastrado com Sucesso!")

    case "Folha de Pagamento":
        st.header("Folha de Pagamento")
        salario = st.number_input("Salário base", min_value=0.0, step=100.0)
        horas_extras = st.number_input("Horas extras", min_value=0.0, step=1.0)
        desconto = st.number_input("Descontos", min_value=0.0, step=50.0)
        total = salario + (horas_extras * 20) - desconto
        st.write(f"💰 Salário líquido: R$ {total:.2f}")

# Benefícios
    case "Benefícios":
        st.header("Gestão de Benefícios")
        plano_saude = st.checkbox("Plano de saúde")
        vale_transporte = st.checkbox("Vale transporte")
        beneficios = []
        if plano_saude: beneficios.append("Plano de saúde")
        if vale_transporte: beneficios.append("Vale transporte")
        st.write("Benefícios ativos:", ", ".join(beneficios) if beneficios else "Nenhum")

# Recrutamento
    case  "Recrutamento":
        st.header("Recrutamento e Seleção")
        vaga = st.text_input("Título da vaga")
        candidato = st.text_input("Nome do candidato")
        if st.button("Registrar candidatura"):
            st.success(f"Candidato {candidato} registrado para a vaga {vaga}!")

# Treinamento
    case "Treinamento":
        st.header("Treinamento e Desenvolvimento")
        curso = st.selectbox("Selecione um curso", ["Excel Avançado", "Liderança", "Comunicação"])
        st.write(f"📚 Curso selecionado: {curso}")

# Desempenho
    case "Desempenho":
        st.header("Avaliação de Desempenho")
        colaborador = st.text_input("Nome do colaborador")
        nota = st.slider("Nota de desempenho", 0, 10, 5)
        if colaborador:
            st.write(f"⭐ {colaborador} recebeu nota {nota}/10")

# Relatórios
    case "Relatórios":
        st.header("Relatórios e Indicadores")
        st.metric("Turnover", "12%", "↓ 2%")
        st.metric("Absenteísmo", "4%", "↑ 1%")
        st.metric("Produtividade", "87%", "↑ 5%")