import streamlit as st
import pandas as pd
import os
from PIL import Image
import google.genai as genai  # biblioteca de api com ia do google
import base64
import numpy as np
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas



client = genai.Client(api_key="AIzaSyD4T5kcEqx6d-SDTmugPQAC_LfSvlD7IX0")  
modelo = "models/gemini-3-flash-preview"  # modelo utilizado para o chatbot

# Função para converter arquivo em base64
def get_base64_of_bin_file(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

img_path = "capsuleSys.png"
img_base64 = get_base64_of_bin_file(img_path)

# CSS para aplicar a imagem como fundo
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/png;base64,{img_base64}");
    background-size: 20%;
    background-position: right;
    background-repeat: no-repeat;
}}
[data-testid="stHeader"] {{
    background: rgba(0,0,0,0);
}}
[data-testid="stToolbar"] {{
    right: 2rem;
}}
</style>
"""
# Aplica o CSS
st.markdown(page_bg_img, unsafe_allow_html=True)

st.title("Capsule Sys")

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
    menu = st.sidebar.radio("Ferramentas", ["Gráficos Gerenciais", "Cadastros", "Almox", "Compras", "Gerencial", "IA", "Contratos", "Desconectar"])

    match menu:
        case "Gráficos Gerenciais":

            df_caixa = pd.read_csv("fluxo_caixa.csv")
            df_caixa["Valor"] = pd.to_numeric(df_caixa["Valor"])
            total_caixa = df_caixa["Valor"].sum()
            st.metric(label="Fluxo de Caixa", value=f"R$ {total_caixa:,.2f}") 

            df_contasp = pd.read_csv("contas_a_pagar.csv")
            df_contasp["Valor"] = pd.to_numeric(df_contasp["Valor"])
            df_abertas = df_contasp[df_contasp["Status"] == "Aberto"]
            total_contasp = df_abertas["Valor"].sum()
            st.metric(label="Contas a Pagar (Abertas)", value=f"R$ {total_contasp:,.2f}")
            st.bar_chart(df_abertas.groupby("Fornecedor")["Valor"].sum())
                
        case "Cadastros":
            cadastro_opcao=st.radio("Escolha uma Opção:", ["Cadastro de Usuário", "Cadastro de Fornecedor", "Cadastro de Produto", "Cadastro Filial"], horizontal=True)
            match cadastro_opcao:
                case "Cadastro de Usuário":    
                    st.write("Cadastro de Usuário")
                    usuario = st.text_input("Usuário")
                    email = st.text_input("E-mail")
                    senha = st.text_input("Senha", type="password")
                    if st.button ("Salvar Usuário"):
                        novo_usuario = pd.DataFrame([{"Usuario":usuario, "E-mail":email, "Senha":senha}])
                        if os.path.exists("usuarios.csv"):
                            novo_usuario.to_csv("usuarios.csv", mode="a", header=False, index=False)
                        else:
                            novo_usuario.to_csv("usuarios.csv", index=False)
                        st.success(f"Usuário Salvo com Sucesso")
                case "Cadastro de Fornecedor":
                    st.write("Cadastro de Fornecedor")
                    nome_fornecedor = st.text_input("Razão Social")
                    email_fornecedor = st.text_input("E-mail")
                    cnpj_fornecedor = st.text_input("CNPJ")
                    contato_fornecedor = st.text_input("Contato")
                    if st.button("Salvar Fornecedor"):
                        novo_fornecedor = pd.DataFrame([{"Nome Fornecedor": nome_fornecedor, "E-mail Fornecedor": email_fornecedor, "CNPJ": cnpj_fornecedor, "Contato Fornecedor": contato_fornecedor}])
                        if os.path.exists("fornecedor.csv"):
                            novo_fornecedor.to_csv("fornecedor.csv", mode="a", header=False, index=False)
                        else:
                            novo_fornecedor.to_csv("fornecedor.csv", index=False)
                        st.success(f"Fornecedor Cadastrado com Sucesso!")
                case "Cadastro de Produto":
                    st.write("Cadastro de Produtos")
                    descricao = st.text_input("Descrição Produto")
                    ean_produto = st.text_input("Código de Barras")
                    preco_produto = st.number_input("Valor Produto", min_value=0.00, step=0.01, format="%.2f")

                    categorias = {
                        "Consumo": ["Alimentos", "Bebidas", "Produtos de limpeza", "Higiene pessoal", "Descartáveis"],
                        "Ferragem": ["Parafusos e pregos", "Ferramentas manuais", "Fixadores", "Fechaduras e cadeados", "Abrasivos"],
                        "Escritório": ["Material de escrita", "Organização", "Equipamentos de escritório", "Mobiliário", "Tecnologia"],
                        "Mecânica": ["Ferramentas de precisão", "Lubrificantes e óleos", "Peças de reposição", "Equipamentos de oficina", "Instrumentos de medição"],
                        "Elétrica": ["Cabos e fios", "Conectores e tomadas", "Iluminação", "Disjuntores e quadros elétricos", "Motores e transformadores"],
                        "Hidráulica": ["Tubos e conexões", "Válvulas e registros", "Bombas hidráulicas", "Torneiras e misturadores", "Reservatórios e caixas d’água"]
                    }

                    categoria_produto = st.selectbox("Defina a Categoria", list(categorias.keys()))
                    subcategoria_produto = st.selectbox("Defina a Subcategoria", categorias[categoria_produto])
                    quantidade_produto = st.number_input("Quantidade", min_value=0)

                    prod_fil = pd.read_csv("filial.csv")
                    opcoes_filiais = ["Todas"] + prod_fil["Nome"].tolist()
                    filial_escolhida = st.selectbox("Filial", opcoes_filiais)

                    if st.button("Salvar Cadastro"):
                        # Calcula o código do produto
                        if os.path.exists("produto.csv"):
                            df_prod = pd.read_csv("produto.csv")
                            ultimo_codigo = df_prod["Codigo"].max()
                            novo_codigo = ultimo_codigo + 1
                        else:
                            novo_codigo = 1

                        if filial_escolhida == "Todas":
                            # Cria uma linha para cada filial
                            lista_produtos = []
                            for nome_filial in prod_fil["Nome"].tolist():
                                lista_produtos.append({
                                    "Codigo": novo_codigo,
                                    "Descrição Produto": descricao,
                                    "ean_produto": ean_produto,
                                    "Preço Produto": preco_produto,
                                    "Categoria": categoria_produto,
                                    "Sub-Categoria": subcategoria_produto,
                                    "Quantidade Produto": quantidade_produto,
                                    "Filial": nome_filial
                                })
                            novo_produto = pd.DataFrame(lista_produtos)
                        else:
                            # Cria apenas uma linha
                            novo_produto = pd.DataFrame([{
                                "Codigo": novo_codigo,
                                "Descrição Produto": descricao,
                                "ean_produto": ean_produto,
                                "Preço Produto": preco_produto,
                                "Categoria": categoria_produto,
                                "Sub-Categoria": subcategoria_produto,
                                "Quantidade Produto": quantidade_produto,
                                "Filial": filial_escolhida
                            }])

                        # Salva no CSV
                        if os.path.exists("produto.csv"):
                            novo_produto.to_csv("produto.csv", mode="a", header=False, index=False)
                        else:
                            novo_produto.to_csv("produto.csv", index=False)

                        st.success(f"Produto código {novo_codigo} cadastrado com sucesso")
                case "Cadastro Filial":
                    st.write("Cadastro de Filial")
                    nome = st.text_input("Descrição Filial")
                    cnpj = st.text_input("CNPJ")
                    endereco = st.text_input("Endereço")
                    codigo = st.text_input("Código Filial")
                    if st.button("Salvar Cadastro"):
                        nova_filial = pd.DataFrame([{"Nome":nome, "CNPJ":cnpj, "Endereço":endereco, "Código":codigo}])
                        if os.path.exists("filial.csv"):
                            nova_filial.to_csv("filial.csv", mode="a", header=False, index=False)
                        else:
                            nova_filial.to_csv("filial.csv", index=False)
                        st.success(f"Filial Cadastrada com Sucesso")                        
        case "Almox":
            st.write("Almoxarifado")
            menu_almox = st.radio(
                "Escolha uma Opção", 
                ["Consulta Estoque", "Requisição de Compras", "Ajuste de Estoque", "Recebimento"], 
                horizontal=True
            )

            match menu_almox:
                case "Consulta Estoque":
                    st.write("Consulta Estoque")
                    painel_estoque = pd.read_csv("produto.csv")
                    st.dataframe(painel_estoque, use_container_width=True)

                case "Requisição de Compras":
                    st.write("Requisição de Compras")

                    # Carrega dados
                    df_produtos = pd.read_csv("produto.csv")
                    produto_escolhido = st.selectbox("Produto", df_produtos["Descrição Produto"].unique().tolist())
                    quantidade = st.number_input("Quantidade", min_value=1)
                    df_filial = pd.read_csv("filial.csv")
                    filial = st.selectbox("Filial Solicitante", df_filial["Nome"].unique().tolist())
                    df_nome_projeto = pd.read_csv("projeto.csv")
                    nome_projeto = st.selectbox("Descrição do Projeto", df_nome_projeto["Descrição"])
                    n_projeto = st.selectbox("Número Projeto; OS", df_nome_projeto["Número Projeto"] )

                    # Inicializa lista de itens
                    if "item_requisicao" not in st.session_state:
                        st.session_state.item_requisicao = []

                    # Botão para adicionar produto
                    if st.button("Adicionar Produto"):
                        item = {
                            "Produto": produto_escolhido,
                            "Quantidade": quantidade,
                            "Filial Requisitante": filial,
                            "Nome Projeto": nome_projeto, "N° Projeto":n_projeto
                        }
                        st.session_state.item_requisicao.append(item)
                        st.success(f"Produto {produto_escolhido} adicionado (Qtd: {quantidade})")

                    # Mostrar itens acumulados
                    if len(st.session_state.item_requisicao) > 0:
                        st.subheader("Itens adicionados à requisição")
                        st.table(pd.DataFrame(st.session_state.item_requisicao))

                    # Botão para salvar requisição inteira
                    if st.button("Salvar Requisição"):
                        if os.path.exists("requisicoes.csv"):
                            df_req = pd.read_csv("requisicoes.csv")
                            ultimo_codigo = df_req["Codigo"].max()
                            novo_codigo = ultimo_codigo + 1
                        else:
                            novo_codigo = 1

                        # Aplica o mesmo código a todos os itens
                        nova_requisicao = pd.DataFrame([
                            {"Codigo": novo_codigo, **item} for item in st.session_state.item_requisicao
                        ])

                        # Salva no CSV
                        if os.path.exists("requisicoes.csv"):
                            nova_requisicao.to_csv("requisicoes.csv", mode="a", header=False, index=False)
                        else:
                            nova_requisicao.to_csv("requisicoes.csv", index=False)
                        st.success(f"Pedido de Compra {novo_codigo} salvo com sucesso")
                    if st.button("Limpar Lista"):
                        st.session_state.item_requisicao = []
                        st.warning("Lista de itens foi limpa.")    

                case "Ajuste de Estoque":
                    st.write("Ajuste de Estoque")            
                    df_produtos = pd.read_csv("produto.csv")
                    ajuste_produto = st.selectbox("Produto", df_produtos["Descrição Produto"].tolist())
                    ajuste_quantidade = st.number_input("Nova Quantidade", min_value=0)
                    ajuste_motivos = st.selectbox("Motivo Ajuste", ["Avaria", "Inventário", "Consumo"])
                    df_filial = pd.read_csv("filial.csv")
                    ajuste_filial = st.selectbox("Filial Ajuste", df_filial["Nome"].tolist())         
                    if st.button("Salvar Ajuste"):
                        ajuste_estoque = pd.DataFrame([{
                            "Produto": ajuste_produto,
                            "Quantidade": ajuste_quantidade,
                            "Motivo Ajuste": ajuste_motivos,
                            "Filial": ajuste_filial
                        }])
                        if os.path.exists("ajuste_estoque.csv"):
                            ajuste_estoque.to_csv("ajuste_estoque.csv", mode="a", header=False, index=False)
                        else:
                            ajuste_estoque.to_csv("ajuste_estoque.csv", index=False)
                        df_produtos.loc[
                            (df_produtos["Descrição Produto"] == ajuste_produto) &
                            (df_produtos["Filial"] == ajuste_filial),
                            "Quantidade Produto"
                        ] = ajuste_quantidade
                        df_produtos.to_csv("produto.csv", index=False)
                        st.success("Ajuste Realizado com Sucesso")
                case "Recebimento":
                    st.write("Recebimento de Mercadorias")

                    # Carrega pedidos já definidos
                    df_pedido = pd.read_csv("vencedores.csv")

                    # Selectbox para escolher o pedido
                    df_pedido["PedidoLabel"] = df_pedido["NumeroPedido"].astype(str) + " - " + df_pedido["Fornecedor"]
                    pedido = st.selectbox("Selecione o Pedido para Recebimento", df_pedido["PedidoLabel"].unique().tolist())

                    # Extrai NumeroPedido e Fornecedor
                    numero_pedido, fornecedor = pedido.split(" - ", 1)
                    df_itens_pedido = df_pedido[
                        (df_pedido["NumeroPedido"].astype(str) == numero_pedido) &
                        (df_pedido["Fornecedor"] == fornecedor)
                    ]

                    st.write("Itens do Pedido:")
                    st.table(df_itens_pedido[["Produto", "Preço Cotado"]])

                    # Carrega produtos atuais
                    df_produto = pd.read_csv("produto.csv")

                    # Selectbox para escolher a filial que está recebendo
                    filiais = df_produto["Filial"].unique().tolist()
                    filial_escolhida = st.selectbox("Selecione a Filial de Entrada", filiais)

                    # Inputs para quantidade recebida
                    recebimentos = {}
                    for _, row in df_itens_pedido.iterrows():
                        qtd_recebida = st.number_input(
                            f"Quantidade recebida de {row['Produto']} na filial {filial_escolhida}",
                            min_value=0,
                            step=1
                        )
                        recebimentos[row["Produto"]] = qtd_recebida

                    if st.button("Confirmar Recebimento"):
                        for produto, qtd in recebimentos.items():
                            if qtd > 0:
                                # Atualiza estoque apenas na filial escolhida
                                df_produto.loc[
                                    (df_produto["Descrição Produto"] == produto) &
                                    (df_produto["Filial"] == filial_escolhida),
                                    "Quantidade Produto"
                                ] += qtd

                        # Salva atualização
                        df_produto.to_csv("produto.csv", index=False)
                        st.success(f"Estoque atualizado com sucesso na filial {filial_escolhida}!")



        case "Compras":
            st.write("Compras")
            escolha_compras= st.radio("Escolha uma Opoção:", ["Gestão de Compras", "Definição de Vencedores", "Pedidos de Compras"], horizontal=True)            
            match escolha_compras:
                case "Gestão de Compras":
                    st.write("Gestão de Compras")
                    df_req_gestao = pd.read_csv("requisicoes.csv")
                    df_req_gestao["Requisicao_Label"] = df_req_gestao["Codigo"].astype(str) + " - " + df_req_gestao["Nome Projeto"]
                    requisicao_compra = st.selectbox("Requisição", df_req_gestao["Requisicao_Label"].unique().tolist())
                    df_req_fornecedor= pd.read_csv("fornecedor.csv")
                    req_fornecedor = st.selectbox("Escolha o Fornecedor", df_req_fornecedor["Nome Fornecedor"])
                    codigo_selecionado = requisicao_compra.split(" - ")[0]
                    data_emissao = st.date_input("Data de Emissão do Pedido")
                    data_recebimento = st.date_input("Data de Recebimento do Pedido")
                    df_requisicao = pd.read_csv("requisicoes.csv")
                    df_filtrada = df_requisicao[df_requisicao["Codigo"] == int(codigo_selecionado)]
                    df_filtrada["Preço Cotado"] = 0.0
                    df_editado = st.data_editor(df_filtrada)
                    if st.button("Salvar Cotação"):
                        df_editado["Requisição"] = requisicao_compra
                        df_editado["Fornecedor"] = req_fornecedor
                        df_editado["Data Emissão"] = data_emissao
                        df_editado["Data Recebimento"] = data_recebimento
                        try:
                            df_existente = pd.read_csv("cotacoes.csv")
                            df_final = pd.concat([df_existente, df_editado], ignore_index=True)
                        except FileNotFoundError:
                            df_final = df_editado
                        df_final.to_csv("cotacoes.csv", index=False)
                        st.success("Cotação salva com sucesso!")
                case "Definição de Vencedores":
                    st.write("Definição de Vencedores")

                    # Carrega cotações
                    df = pd.read_csv("cotacoes.csv")

                    # Selectbox para escolher código da requisição
                    codigos_unicos = df["Codigo"].unique().tolist()
                    codigo_escolhido = st.selectbox("Escolha o Código da Requisição", codigos_unicos)

                    # Filtra apenas as cotações desse código
                    df_filtrado = df[df["Codigo"] == codigo_escolhido]

                    # Cria tabela comparativa: Produto x Fornecedor
                    tabela = df_filtrado.pivot_table(
                        index="Produto",
                        columns="Fornecedor",
                        values="Preço Cotado"
                    )

                    # Função para destacar menor preço em verde
                    def highlight_min(s):
                        is_min = s == s.min()
                        return ['background-color: lightgreen' if v else '' for v in is_min]

                    st.write("Comparativo de Cotações")
                    st.dataframe(tabela.style.apply(highlight_min, axis=1), use_container_width=True)

                    # Checkboxes para definir vencedores
                    st.write("Definir Vencedores")
                    vencedores = {}
                    for produto, linha in tabela.iterrows():
                        fornecedor_min = linha.idxmin()
                        st.write(f"Produto: {produto}")
                        for fornecedor, valor in linha.items():
                            default = (fornecedor == fornecedor_min)  # pré-seleciona o menor preço
                            vencedores[(produto, fornecedor)] = st.checkbox(
                                f"{fornecedor} - R$ {valor:.2f}", value=default, key=f"{produto}_{fornecedor}"
                            )

                    # Botão para salvar vencedores
                    if st.button("Definir Vencedores"):
                        selecionados = [
                        {
                            "Produto": prod,
                            "Fornecedor": forn,
                            "Preço Cotado": float(tabela.loc[prod, forn]),
                            "Selecionado": True
                        }
                        for (prod, forn), marcado in vencedores.items() if marcado
                    ]

                        if selecionados:
                            df_vencedores = pd.DataFrame(selecionados)

                        # Se já existe arquivo, carrega para descobrir último código
                        if os.path.exists("vencedores.csv"):
                            df_existente = pd.read_csv("vencedores.csv")
                            if "NumeroPedido" in df_existente.columns:
                                ultimo_numero = df_existente["NumeroPedido"].max()
                            else:
                                ultimo_numero = 0  # se não existir, começa do zero
                            proximo_numero = ultimo_numero + 1
                        else:
                            proximo_numero = 1

                        df_vencedores["NumeroPedido"] = proximo_numero

                        # Salva no CSV
                        if os.path.exists("vencedores.csv"):
                            df_vencedores.to_csv("vencedores.csv", mode="a", header=False, index=False)
                        else:
                            df_vencedores.to_csv("vencedores.csv", index=False)

                        st.success(f"Vencedores definidos com sucesso! Número do pedido: {proximo_numero}")


                    # Botão para emitir pedido em PDF
                    if st.button("Emitir Pedido de Compra"):
                        try:
                            df_vencedores = pd.read_csv("vencedores.csv")
                            numero_pedido = df_vencedores["NumeroPedido"].max()  # pega o último número

                            buffer = io.BytesIO()
                            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
                            elementos = []

                            # Logo da CapsuleSys (coloque o arquivo na pasta do projeto)
                            logo = Image("capsuleSys.png", width=120, height=50)
                            elementos.append(logo)
                            elementos.append(Spacer(1, 20))

                            estilos = getSampleStyleSheet()
                            titulo = Paragraph(f"Pedido de Compra Nº {numero_pedido}", estilos["Title"])
                            elementos.append(titulo)
                            elementos.append(Spacer(1, 20))

                            # Monta tabela com vencedores do último pedido
                            dados = [["Produto", "Fornecedor", "Preço Cotado"]]
                            for _, row in df_vencedores[df_vencedores["NumeroPedido"] == numero_pedido].iterrows():
                                dados.append([row["Produto"], row["Fornecedor"], f"R$ {row['Preço Cotado']:.2f}"])

                            tabela_pdf = Table(dados, colWidths=[400, 250, 100])
                            tabela_pdf.setStyle(TableStyle([
                                ("BACKGROUND", (0,0), (-1,0), colors.grey),
                                ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
                                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                                ("BOTTOMPADDING", (0,0), (-1,0), 12),
                                ("BACKGROUND", (0,1), (-1,-1), colors.beige),
                                ("GRID", (0,0), (-1,-1), 1, colors.black),
                            ]))
                            elementos.append(tabela_pdf)

                            doc.build(elementos)
                            buffer.seek(0)

                            st.download_button(
                                label="📄 Baixar Pedido de Compra (PDF)",
                                data=buffer,
                                file_name=f"pedido_compra_{numero_pedido}.pdf",
                                mime="application/pdf"
                            )
                            st.success(f"Pedido de compra Nº {numero_pedido} gerado com sucesso!")
                        except FileNotFoundError:
                            st.error("Nenhum vencedor definido ainda. Clique em 'Definir Vencedores' primeiro.")



                case "Pedidos de Compras":
                    st.write("Pedidos de Compras")
                    df_pedido = pd.read_csv("vencedores.csv")

                    # Cria coluna com NumeroPedido + Fornecedor
                    df_pedido["PedidoLabel"] = df_pedido["NumeroPedido"].astype(str) + " - " + df_pedido["Fornecedor"]

                    pedido = st.selectbox("Selecione um Pedido de Compra", df_pedido["PedidoLabel"].unique().tolist())

                    # Gera PDF
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
                    elementos = []

                    logo = Image("capsuleSys.png", width=120, height=50)
                    elementos.append(logo)
                    elementos.append(Spacer(1, 20))

                    estilos = getSampleStyleSheet()
                    titulo = Paragraph(f"Pedido de Compra {pedido}", estilos["Title"])
                    elementos.append(titulo)
                    elementos.append(Spacer(1, 20))

                    # Extrai NumeroPedido e Fornecedor
                    numero_pedido, fornecedor = pedido.split(" - ", 1)

                    dados = [["Produto", "Fornecedor", "Preço Cotado"]]
                    for _, row in df_pedido[
                        (df_pedido["NumeroPedido"].astype(str) == numero_pedido) &
                        (df_pedido["Fornecedor"] == fornecedor)
                    ].iterrows():
                        dados.append([row["Produto"], row["Fornecedor"], f"R$ {row['Preço Cotado']:.2f}"])

                    tabela_pdf = Table(dados, colWidths=[400, 250, 100])
                    tabela_pdf.setStyle(TableStyle([
                        ("BACKGROUND", (0,0), (-1,0), colors.grey),
                        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
                        ("ALIGN", (0,0), (-1,-1), "CENTER"),
                        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0,0), (-1,0), 12),
                        ("BACKGROUND", (0,1), (-1,-1), colors.beige),
                        ("GRID", (0,0), (-1,-1), 1, colors.black),
                    ]))
                    elementos.append(tabela_pdf)

                    doc.build(elementos)
                    buffer.seek(0)

                    st.download_button(
                        label="📄 Baixar Pedido de Compra (PDF)",
                        data=buffer,
                        file_name=f"pedido_compra_{numero_pedido}_{fornecedor}.pdf",
                        mime="application/pdf"
                    )

        case "Gerencial":
            st.write("Gerencial")
            op_gerencial=st.radio("Escolha uma Opção:", ["Fluxo de Caixa", "Contas a Pagar", "Contas a Receber", "Relatórios Gerenciais"], horizontal=True)
            match op_gerencial:
                case "Fluxo de Caixa":
                    fluxo_caixa=st.number_input("Valor a Cadastrar")
                    valor = pd.DataFrame([{"Valor":fluxo_caixa}])
                    if st.button("Salvar Valor"):
                        if os.path.exists("fluxo_caixa.csv"):
                            valor.to_csv("fluxo_caixa.csv", mode="a", header=False, index=False)
                        else:
                            valor.to_csv("fluxo_caixa.csv", index=False)
                        st.success("Valor Cadastrado com Sucesso")
                case "Contas a Pagar":
                    st.subheader("Cadastrar Conta a Pagar")
                    nota_fiscal = st.text_input("N° Nota Fiscal")
                    df_recebedor = pd.read_csv("fornecedor.csv")
                    recebedor = st.selectbox("Fornecedor", df_recebedor["Nome Fornecedor"])
                    valor = st.number_input("Valor", min_value=0.0, step=0.01)
                    vencimento = st.date_input("Data de Vencimento")
                    n_faturas = st.text_input("Quantidade de Faturas")

                    nova_fatura = pd.DataFrame([{
                        "NF": nota_fiscal,
                        "Fornecedor": recebedor,
                        "Valor": valor,
                        "Vencimento": vencimento,
                        "QTD Faturas": n_faturas,
                        "Status": "Aberto"
                    }])

                    if st.button("Salvar Fatura"):
                        if os.path.exists("contas_a_pagar.csv"):
                            nova_fatura.to_csv("contas_a_pagar.csv", mode="a", header=False, index=False)
                        else:
                            nova_fatura.to_csv("contas_a_pagar.csv", index=False)
                        st.success("Fatura salva com sucesso!")

                    # Visualização e marcação como paga
                    if os.path.exists("contas_a_pagar.csv"):
                        df_pagar = pd.read_csv("contas_a_pagar.csv")
                        st.subheader("Faturas em Aberto")
                        faturas_abertas = df_pagar[df_pagar["Status"] == "Aberto"]
                        for i, row in faturas_abertas.iterrows():
                            st.write(f"NF: {row['NF']} | Fornecedor: {row['Fornecedor']} | Valor: R$ {row['Valor']:.2f} | Vencimento: {row['Vencimento']}")
                            if st.button(f"Marcar como Paga - NF {row['NF']}"):
                                df_pagar.at[i, "Status"] = "Pago"
                                df_pagar.to_csv("contas_a_pagar.csv", index=False)
                                st.success(f"Fatura {row['NF']} marcada como paga!")

                case "Contas a Receber":
                    st.subheader("Cadastrar Conta a Receber")
                    contrato = st.text_input("N° Contrato")
                    df_cliente = pd.read_csv("fornecedor.csv")
                    cliente = st.selectbox("Cliente", df_cliente["Nome Fornecedor"])
                    valor = st.number_input("Valor", min_value=0.0, step=0.01)
                    vencimento = st.date_input("Data de Vencimento")
                    n_faturas = st.text_input("Quantidade de Faturas")

                    nova_receita = pd.DataFrame([{
                        "Contrato": contrato,
                        "Cliente": cliente,
                        "Valor": valor,
                        "Vencimento": vencimento,
                        "QTD Faturas": n_faturas,
                        "Status": "Aberto"
                    }])

                    if st.button("Salvar Fatura"):
                        if os.path.exists("contas_a_receber.csv"):
                            nova_receita.to_csv("contas_a_receber.csv", mode="a", header=False, index=False)
                        else:
                            nova_receita.to_csv("contas_a_receber.csv", index=False)
                        st.success("Fatura salva com sucesso!")

                    # Visualização e marcação como recebida
                    if os.path.exists("contas_a_receber.csv"):
                        df_receber = pd.read_csv("contas_a_receber.csv")
                        st.subheader("Faturas em Aberto")
                        faturas_abertas = df_receber[df_receber["Status"] == "Aberto"]
                        for i, row in faturas_abertas.iterrows():
                            st.write(f"Contrato: {row['Contrato']} | Cliente: {row['Cliente']} | Valor: R$ {row['Valor']:.2f} | Vencimento: {row['Vencimento']}")
                            if st.button(f"Marcar como Recebida - Contrato {row['Contrato']}"):
                                df_receber.at[i, "Status"] = "Recebido"
                                df_receber.to_csv("contas_a_receber.csv", index=False)
                                st.success(f"Fatura do contrato {row['Contrato']} marcada como recebida!")

                case "Relatórios Gerenciais":
                    st.write("Relatórios Gerenciais")
                     
        case "IA":  
            st.subheader("ATLAS IA")
            if "lista_mensagem" not in st.session_state: 
                st.session_state["lista_mensagem"] = []

            # exibe histórico
            for mensagem in st.session_state["lista_mensagem"]:
                st.chat_message(mensagem["role"]).write(mensagem["content"])

            texto_user = st.chat_input("Digite Sua Mensagem")

            if texto_user:
                # adiciona mensagem do usuário
                st.chat_message("user").write(texto_user)
                st.session_state["lista_mensagem"].append({"role": "user", "content": texto_user})

                # converter para formato aceito pela API
                mensagens = []
                for msg in st.session_state["lista_mensagem"]:
                    mensagens.append({"role": msg["role"],"parts": [{"text": msg["content"]}]})

                # chamada à API
                resposta_ia = client.models.generate_content(model=modelo, contents=mensagens)
                texto_resposta_ia = resposta_ia.text

                # exibe resposta
                st.chat_message("assistant").write(texto_resposta_ia)
                st.session_state["lista_mensagem"].append({"role": "assistant", "content": texto_resposta_ia})

        case "Contratos":
            escolha_contratos=st.radio("Escolha uma opção:", ["Cadastro de Projeto","Emissão de Contratos", "Controle de Contratos", "Gestão de Contratos"], horizontal=True)
            match escolha_contratos:
                case "Cadastro de Projeto":
                    st.write("Cadastro de Projeto")
                    nome_projeto=st.text_input("Nome do Projeto")
                    n_projeto=st.text_input("Número do Projeto")
                    valor_projeto=st.number_input("Valor previsto")
                    df_projeto = pd.DataFrame([{"Descrição":nome_projeto, "Número Projeto":n_projeto, "Valor":valor_projeto}])
                    if st.button("Salvar Projeto"):
                        if os.path.exists("projeto.csv"):
                            df_projeto.to_csv("projeto.csv", mode="a", header=False, index=False)
                        else:
                            df_projeto.to_csv("projeto.csv", index=False)
                        st.success("Projeto Salvo com Sucesso")        

                case "Emissão de Contratos":
                    df_contrato_projeto = pd.read_csv("projeto.csv")
                    contrato_projeto = st.selectbox("Projeto", df_contrato_projeto["Descrição"])
                    empresa_contratante = st.selectbox("Empresa Contratante", ["DigiEvo Tech System"])
                    cnpj_empresa_contratante = st.selectbox("CNPJ Contratante", ["11.111.111/1111-11"])
                    df_fornecedor_contrato = pd.read_csv("fornecedor.csv")
                    contrato_fornecedor = st.selectbox("Escolha o Fornecedor", df_fornecedor_contrato["Nome Fornecedor"])
                    cnpj_empresa_fornecedor = st.selectbox("CNPJ Fornecedor", df_fornecedor_contrato["CNPJ"])
                    contrato_objeto = st.text_area("Objeto do Contrato")
                    valor_contrato = st.number_input("Valor Contrato")
                    contrato_inicio=st.date_input("Data de Inicio")
                    contrato_fim=st.date_input("Data de Conclusão")
                    df_contrato = pd.DataFrame([{"Empresa Contratante":empresa_contratante, "CNPJ Contratante":cnpj_empresa_contratante, "CNPJ Fornecedor":cnpj_empresa_fornecedor,
                    "Objeto":contrato_objeto, "Valor":valor_contrato, "Data Inicio": contrato_inicio, "Data Fim": contrato_fim, "Projeto":contrato_projeto}])
                    if st.button("Salvar Contrato"):
                        if os.path.exists("contrato.csv"):
                            df_contrato.to_csv("contrato.csv", mode="a", header=False, index=False)
                        else:
                            df_contrato.to_csv("contrato.csv", index=False)
                        st.success("Contrato Salvo com Sucesso")
                    if st.button("Emitir Contrato PDF"):
                        df_contrato_pdf = pd.read_csv("contrato.csv")
                        contrato_pdf = df_contrato_pdf.iloc[-1]  # pega o último contrato salvo

                        # cria o canvas
                        c = canvas.Canvas("contrato.pdf", pagesize=A4)
                        largura, altura = A4

                        # título
                        c.setFont("Helvetica-Bold", 16)
                        c.drawCentredString(largura/2, altura - 50, "CONTRATO DE PRESTAÇÃO DE SERVIÇOS")

                        c.setFont("Helvetica", 12)
                        linha = altura - 100
                        espaco = 20

                        # dados principais
                        c.drawString(50, linha, f"Projeto: {contrato_pdf['Projeto']}"); linha -= espaco
                        c.drawString(50, linha, f"Empresa Contratante: {contrato_pdf['Empresa Contratante']}"); linha -= espaco
                        c.drawString(50, linha, f"CNPJ Contratante: {contrato_pdf['CNPJ Contratante']}"); linha -= espaco
                        c.drawString(50, linha, f"Fornecedor: {contrato_pdf['Fornecedor']}"); linha -= espaco
                        c.drawString(50, linha, f"CNPJ Fornecedor: {contrato_pdf['CNPJ Fornecedor']}"); linha -= espaco
                        c.drawString(50, linha, f"Objeto: {contrato_pdf['Objeto']}"); linha -= espaco
                        c.drawString(50, linha, f"Valor: R$ {contrato_pdf['Valor']:.2f}"); linha -= espaco
                        c.drawString(50, linha, f"Data de Início: {contrato_pdf['Data Inicio']}"); linha -= espaco
                        c.drawString(50, linha, f"Data de Conclusão: {contrato_pdf['Data Fim']}"); linha -= espaco

                        # assinaturas
                        linha -= 60
                        c.drawString(50, linha, "________________________________________"); linha -= espaco
                        c.drawString(50, linha, "Assinatura da Empresa Contratante")

                        linha -= 60
                        c.drawString(50, linha, "________________________________________"); linha -= espaco
                        c.drawString(50, linha, "Assinatura do Fornecedor")
                        # salva o PDF
                        c.save()
                        st.success("Contrato emitido em PDF com sucesso!")
        case "Desconectar": 
          st.session_state["logado"]=False  
          st.rerun()  

  