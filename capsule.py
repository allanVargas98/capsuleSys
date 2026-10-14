import streamlit as st
import pandas as pd
import os
from PIL import Image
import google.genai as genai
import base64
import numpy as np
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from supabase import create_client, Client

SUPABASE_URL = "https://vhhpetifyuawfiuzdrsu.supabase.co"
SUPABASE_KEY = "sb_publishable_2UpNmtRVpMTMXwYYa_0Kkw_oPc5A2jR"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

client = genai.Client(api_key="AIzaSyD4T5kcEqx6d-SDTmugPQAC_LfSvlD7IX0")  
modelo = "models/gemini-3-flash-preview"

def get_base64_of_bin_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    return ""

img_path = "capsuleSys.png"
img_base64 = get_base64_of_bin_file(img_path)

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
st.markdown(page_bg_img, unsafe_allow_html=True)

st.title("Capsule Sys")

def tela_login():
    st.title("Login")
    Usuario = st.text_input("Usuário", value="admin")
    Senha = st.text_input("Senha", type="password", value="1234")

    if st.button("Entrar"):
        st.session_state["logado"] = True
        st.session_state["usuario"] = Usuario if Usuario else "admin"
        st.rerun()

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
else:
    menu = st.sidebar.radio("Ferramentas", ["Gráficos Gerenciais", "Cadastros", "Almox", "Compras", "Gerencial", "IA", "Contratos", "Desconectar"])

    match menu:
        case "Gráficos Gerenciais":
            try:
                df_caixa = pd.DataFrame(supabase.table("fluxo_caixa").select("*").execute().data)
                if not df_caixa.empty and "Valor" in df_caixa.columns:
                    df_caixa["Valor"] = pd.to_numeric(df_caixa["Valor"])
                    total_caixa = df_caixa["Valor"].sum()
                    st.metric(label="Fluxo de Caixa", value=f"R$ {total_caixa:,.2f}") 
                else:
                    st.metric(label="Fluxo de Caixa", value="R$ 0,00")
            except Exception:
                st.metric(label="Fluxo de Caixa", value="R$ 0,00")

            try:
                df_contasp = pd.DataFrame(supabase.table("contas_a_pagar").select("*").execute().data)
                if not df_contasp.empty and "Valor" in df_contasp.columns and "Status" in df_contasp.columns:
                    df_contasp["Valor"] = pd.to_numeric(df_contasp["Valor"])
                    df_abertas = df_contasp[df_contasp["Status"] == "Aberto"]
                    total_contasp = df_abertas["Valor"].sum()
                    st.metric(label="Contas a Pagar (Abertas)", value=f"R$ {total_contasp:,.2f}")
                    if not df_abertas.empty:
                        st.bar_chart(df_abertas.groupby("Fornecedor")["Valor"].sum())
                else:
                    st.metric(label="Contas a Pagar (Abertas)", value="R$ 0,00")
            except Exception:
                st.metric(label="Contas a Pagar (Abertas)", value="R$ 0,00")
                
        case "Cadastros":
            cadastro_opcao = st.radio("Escolha uma Opção:", ["Cadastro de Usuário", "Cadastro de Fornecedor", "Cadastro de Produto", "Cadastro Filial"], horizontal=True)
            match cadastro_opcao:
                case "Cadastro de Usuário":    
                    st.write("Cadastro de Usuário")
                    usuario = st.text_input("Usuário")
                    email = st.text_input("E-mail")
                    senha = st.text_input("Senha", type="password")
                    if st.button("Salvar Usuário"):
                        if usuario and email and senha:
                            try:
                                supabase.table("usuarios").insert({
                                    "Usuario": usuario,
                                    "E-mail": email,
                                    "Senha": senha
                                }).execute()
                                st.success("Usuário Salvo com Sucesso no Supabase!")
                            except Exception as e:
                                st.error(f"Erro ao salvar usuário: {e}")
                        else:
                            st.warning("Preencha todos os campos.")

                case "Cadastro de Fornecedor":
                    st.write("Cadastro de Fornecedor")
                    nome_fornecedor = st.text_input("Razão Social")
                    email_fornecedor = st.text_input("E-mail")
                    cnpj_fornecedor = st.text_input("CNPJ")
                    contato_fornecedor = st.text_input("Contato")
                    if st.button("Salvar Fornecedor"):
                        try:
                            supabase.table("fornecedor").insert({
                                "Nome Fornecedor": nome_fornecedor,
                                "E-mail Fornecedor": email_fornecedor,
                                "CNPJ": cnpj_fornecedor,
                                "Contato Fornecedor": contato_fornecedor
                            }).execute()
                            st.success("Fornecedor Cadastrado com Sucesso no Supabase!")
                        except Exception as e:
                            st.error(f"Erro ao salvar fornecedor: {e}")

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

                    try:
                        df_fil = pd.DataFrame(supabase.table("filial").select("*").execute().data)
                        opcoes_filiais = ["Todas"] + (df_fil["Nome"].tolist() if not df_fil.empty and "Nome" in df_fil.columns else [])
                    except Exception:
                        opcoes_filiais = ["Todas"]

                    filial_escolhida = st.selectbox("Filial", opcoes_filiais)

                    if st.button("Salvar Cadastro"):
                        try:
                            res_prod = supabase.table("produto").select("Codigo").order("Codigo", desc=True).limit(1).execute()
                            dados_ult = res_prod.data
                            novo_codigo = (dados_ult[0]["Codigo"] + 1) if dados_ult and "Codigo" in dados_ult[0] else 1
                        except Exception:
                            novo_codigo = 1

                        lista_produtos = []
                        if filial_escolhida == "Todas" and not df_fil.empty:
                            for nome_filial in df_fil["Nome"].tolist():
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
                        else:
                            lista_produtos.append({
                                "Codigo": novo_codigo,
                                "Descrição Produto": descricao,
                                "ean_produto": ean_produto,
                                "Preço Produto": preco_produto,
                                "Categoria": categoria_produto,
                                "Sub-Categoria": subcategoria_produto,
                                "Quantidade Produto": quantidade_produto,
                                "Filial": filial_escolhida
                            })

                        try:
                            supabase.table("produto").insert(lista_produtos).execute()
                            st.success(f"Produto código {novo_codigo} cadastrado com sucesso no Supabase!")
                        except Exception as e:
                            st.error(f"Erro ao salvar produto: {e}")

                case "Cadastro Filial":
                    st.write("Cadastro de Filial")
                    nome = st.text_input("Descrição Filial")
                    cnpj = st.text_input("CNPJ")
                    endereco = st.text_input("Endereço")
                    codigo = st.text_input("Código Filial")
                    if st.button("Salvar Cadastro"):
                        try:
                            supabase.table("filial").insert({
                                "Nome": nome,
                                "CNPJ": cnpj,
                                "Endereço": endereco,
                                "Código": codigo
                            }).execute()
                            st.success("Filial Cadastrada com Sucesso no Supabase!")
                        except Exception as e:
                            st.error(f"Erro ao salvar filial: {e}")                        

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
                    try:
                        res = supabase.table("produto").select("*").execute()
                        painel_estoque = pd.DataFrame(res.data)
                        if not painel_estoque.empty:
                            st.dataframe(painel_estoque, use_container_width=True)
                        else:
                            st.info("Nenhum produto cadastrado no Supabase.")
                    except Exception as e:
                        st.error(f"Erro ao carregar estoque: {e}")

                case "Requisição de Compras":
                    st.write("Requisição de Compras")
                    try:
                        df_produtos = pd.DataFrame(supabase.table("produto").select("*").execute().data)
                        df_filial = pd.DataFrame(supabase.table("filial").select("*").execute().data)
                        df_nome_projeto = pd.DataFrame(supabase.table("projeto").select("*").execute().data)

                        prod_lista = df_produtos["Descrição Produto"].unique().tolist() if not df_produtos.empty else []
                        fil_lista = df_filial["Nome"].unique().tolist() if not df_filial.empty else []
                        proj_desc = df_nome_projeto["Descrição"].tolist() if not df_nome_projeto.empty else []
                        proj_num = df_nome_projeto["Número Projeto"].tolist() if not df_nome_projeto.empty else []

                        produto_escolhido = st.selectbox("Produto", prod_lista)
                        quantidade = st.number_input("Quantidade", min_value=1)
                        filial = st.selectbox("Filial Solicitante", fil_lista)
                        nome_projeto = st.selectbox("Descrição do Projeto", proj_desc)
                        n_projeto = st.selectbox("Número Projeto; OS", proj_num)

                        if "item_requisicao" not in st.session_state:
                            st.session_state.item_requisicao = []

                        if st.button("Adicionar Produto"):
                            item = {
                                "Produto": produto_escolhido,
                                "Quantidade": quantidade,
                                "Filial Requisitante": filial,
                                "Nome Projeto": nome_projeto, 
                                "N° Projeto": n_projeto
                            }
                            st.session_state.item_requisicao.append(item)
                            st.success(f"Produto {produto_escolhido} adicionado (Qtd: {quantidade})")

                        if len(st.session_state.item_requisicao) > 0:
                            st.subheader("Itens adicionados à requisição")
                            st.table(pd.DataFrame(st.session_state.item_requisicao))

                        if st.button("Salvar Requisição"):
                            try:
                                res_req = supabase.table("requisicoes").select("Codigo").order("Codigo", desc=True).limit(1).execute()
                                ult_req = res_req.data
                                novo_codigo = (ult_req[0]["Codigo"] + 1) if ult_req and "Codigo" in ult_req[0] else 1
                            except Exception:
                                novo_codigo = 1

                            nova_requisicao = [
                                {"Codigo": novo_codigo, **item} for item in st.session_state.item_requisicao
                            ]
                            supabase.table("requisicoes").insert(nova_requisicao).execute()
                            st.success(f"Pedido de Compra {novo_codigo} salvo com sucesso no Supabase!")

                        if st.button("Limpar Lista"):
                            st.session_state.item_requisicao = []
                            st.warning("Lista de itens foi limpa.")
                    except Exception as e:
                        st.error(f"Erro na requisição: {e}")

                case "Ajuste de Estoque":
                    st.write("Ajuste de Estoque")
                    try:
                        df_produtos = pd.DataFrame(supabase.table("produto").select("*").execute().data)
                        df_filial = pd.DataFrame(supabase.table("filial").select("*").execute().data)

                        prod_lista = df_produtos["Descrição Produto"].tolist() if not df_produtos.empty else []
                        fil_lista = df_filial["Nome"].tolist() if not df_filial.empty else []

                        ajuste_produto = st.selectbox("Produto", prod_lista)
                        ajuste_quantidade = st.number_input("Nova Quantidade", min_value=0)
                        ajuste_motivos = st.selectbox("Motivo Ajuste", ["Avaria", "Inventário", "Consumo"])
                        ajuste_filial = st.selectbox("Filial Ajuste", fil_lista)         

                        if st.button("Salvar Ajuste"):
                            supabase.table("ajuste_estoque").insert({
                                "Produto": ajuste_produto,
                                "Quantidade": ajuste_quantidade,
                                "Motivo Ajuste": ajuste_motivos,
                                "Filial": ajuste_filial
                            }).execute()

                            supabase.table("produto").update({"Quantidade Produto": ajuste_quantidade}).eq("Descrição Produto", ajuste_produto).eq("Filial", ajuste_filial).execute()
                            st.success("Ajuste Realizado com Sucesso no Supabase!")
                    except Exception as e:
                        st.error(f"Erro no ajuste de estoque: {e}")

                case "Recebimento":
                    st.write("Recebimento de Mercadorias")
                    try:
                        df_pedido = pd.DataFrame(supabase.table("vencedores").select("*").execute().data)
                        if not df_pedido.empty:
                            df_pedido["PedidoLabel"] = df_pedido["NumeroPedido"].astype(str) + " - " + df_pedido["Fornecedor"]
                            pedido = st.selectbox("Selecione o Pedido para Recebimento", df_pedido["PedidoLabel"].unique().tolist())

                            numero_pedido, fornecedor = pedido.split(" - ", 1)
                            df_itens_pedido = df_pedido[
                                (df_pedido["NumeroPedido"].astype(str) == numero_pedido) &
                                (df_pedido["Fornecedor"] == fornecedor)
                            ]

                            st.write("Itens do Pedido:")
                            st.table(df_itens_pedido[["Produto", "Preço Cotado"]])

                            df_produto = pd.DataFrame(supabase.table("produto").select("*").execute().data)
                            filiais = df_produto["Filial"].unique().tolist() if not df_produto.empty else []
                            filial_escolhida = st.selectbox("Selecione a Filial de Entrada", filiais)

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
                                        res_q = supabase.table("produto").select("id, Quantidade Produto").eq("Descrição Produto", produto).eq("Filial", filial_escolhida).execute()
                                        if res_q.data:
                                            row_p = res_q.data[0]
                                            novo_total = row_p["Quantidade Produto"] + qtd
                                            supabase.table("produto").update({"Quantidade Produto": novo_total}).eq("id", row_p["id"]).execute()
                                st.success(f"Estoque atualizado com sucesso na filial {filial_escolhida}!")
                        else:
                            st.info("Nenhum pedido de vencedor encontrado.")
                    except Exception as e:
                        st.error(f"Erro no recebimento: {e}")

        case "Compras":
            st.write("Compras")
            escolha_compras = st.radio("Escolha uma Opção:", ["Gestão de Compras", "Definição de Vencedores", "Pedidos de Compras"], horizontal=True)            
            match escolha_compras:
                case "Gestão de Compras":
                    st.write("Gestão de Compras")
                    try:
                        df_req_gestao = pd.DataFrame(supabase.table("requisicoes").select("*").execute().data)
                        df_req_fornecedor = pd.DataFrame(supabase.table("fornecedor").select("*").execute().data)

                        if not df_req_gestao.empty and not df_req_fornecedor.empty:
                            df_req_gestao["Requisicao_Label"] = df_req_gestao["Codigo"].astype(str) + " - " + df_req_gestao["Nome Projeto"]
                            requisicao_compra = st.selectbox("Requisição", df_req_gestao["Requisicao_Label"].unique().tolist())
                            req_fornecedor = st.selectbox("Escolha o Fornecedor", df_req_fornecedor["Nome Fornecedor"])
                            codigo_selecionado = requisicao_compra.split(" - ")[0]
                            data_emissao = st.date_input("Data de Emissão do Pedido")
                            data_recebimento = st.date_input("Data de Recebimento do Pedido")

                            df_filtrada = df_req_gestao[df_req_gestao["Codigo"] == int(codigo_selecionado)].copy()
                            df_filtrada["Preço Cotado"] = 0.0
                            df_editado = st.data_editor(df_filtrada)

                            if st.button("Salvar Cotação"):
                                df_editado["Requisição"] = requisicao_compra
                                df_editado["Fornecedor"] = req_fornecedor
                                df_editado["Data Emissão"] = str(data_emissao)
                                df_editado["Data Recebimento"] = str(data_recebimento)
                                
                                dados_inserir = df_editado.to_dict(orient="records")
                                supabase.table("cotacoes").insert(dados_inserir).execute()
                                st.success("Cotação salva com sucesso no Supabase!")
                        else:
                            st.info("Cadastre requisições e fornecedores primeiro.")
                    except Exception as e:
                        st.error(f"Erro na gestão de compras: {e}")

                case "Definição de Vencedores":
                    st.write("Definição de Vencedores")
                    try:
                        df = pd.DataFrame(supabase.table("cotacoes").select("*").execute().data)
                        if not df.empty:
                            codigos_unicos = df["Codigo"].unique().tolist()
                            codigo_escolhido = st.selectbox("Escolha o Código da Requisição", codigos_unicos)

                            df_filtrado = df[df["Codigo"] == codigo_escolhido]
                            tabela = df_filtrado.pivot_table(
                                index="Produto",
                                columns="Fornecedor",
                                values="Preço Cotado"
                            )

                            def highlight_min(s):
                                is_min = s == s.min()
                                return ['background-color: lightgreen' if v else '' for v in is_min]

                            st.write("Comparativo de Cotações")
                            st.dataframe(tabela.style.apply(highlight_min, axis=1), use_container_width=True)

                            st.write("Definir Vencedores")
                            vencedores = {}
                            for produto, linha in tabela.iterrows():
                                fornecedor_min = linha.idxmin()
                                st.write(f"Produto: {produto}")
                                for fornecedor, valor in linha.items():
                                    default = (fornecedor == fornecedor_min)
                                    vencedores[(produto, fornecedor)] = st.checkbox(
                                        f"{fornecedor} - R$ {valor:.2f}", value=default, key=f"{produto}_{fornecedor}"
                                    )

                            if st.button("Definir Vencedores"):
                                try:
                                    res_v = supabase.table("vencedores").select("NumeroPedido").order("NumeroPedido", desc=True).limit(1).execute()
                                    ult_v = res_v.data
                                    proximo_numero = (ult_v[0]["NumeroPedido"] + 1) if ult_v and "NumeroPedido" in ult_v[0] else 1
                                except Exception:
                                    proximo_numero = 1

                                selecionados = [
                                    {
                                        "Produto": prod,
                                        "Fornecedor": forn,
                                        "Preço Cotado": float(tabela.loc[prod, forn]),
                                        "Selecionado": True,
                                        "NumeroPedido": proximo_numero
                                    }
                                    for (prod, forn), marcado in vencedores.items() if marcado
                                ]

                                if selecionados:
                                    supabase.table("vencedores").insert(selecionados).execute()
                                    st.success(f"Vencedores definidos com sucesso! Número do pedido: {proximo_numero}")
                        else:
                            st.info("Nenhuma cotação registrada.")
                    except Exception as e:
                        st.error(f"Erro ao definir vencedores: {e}")

                case "Pedidos de Compras":
                    st.write("Pedidos de Compras")
                    try:
                        df_pedido = pd.DataFrame(supabase.table("vencedores").select("*").execute().data)
                        if not df_pedido.empty:
                            df_pedido["PedidoLabel"] = df_pedido["NumeroPedido"].astype(str) + " - " + df_pedido["Fornecedor"]
                            pedido = st.selectbox("Selecione um Pedido de Compra", df_pedido["PedidoLabel"].unique().tolist())

                            numero_pedido, fornecedor = pedido.split(" - ", 1)

                            buffer = io.BytesIO()
                            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
                            elementos = []

                            if os.path.exists("capsuleSys.png"):
                                logo = Image("capsuleSys.png", width=120, height=50)
                                elementos.append(logo)
                                elementos.append(Spacer(1, 20))

                            estilos = getSampleStyleSheet()
                            titulo = Paragraph(f"Pedido de Compra {pedido}", estilos["Title"])
                            elementos.append(titulo)
                            elementos.append(Spacer(1, 20))

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
                        else:
                            st.info("Nenhum pedido gerado.")
                    except Exception as e:
                        st.error(f"Erro ao gerar pedido: {e}")

        case "Gerencial":
            st.write("Gerencial")
            op_gerencial = st.radio("Escolha uma Opção:", ["Fluxo de Caixa", "Contas a Pagar", "Contas a Receber", "Relatórios Gerenciais"], horizontal=True)
            match op_gerencial:
                case "Fluxo de Caixa":
                    fluxo_caixa = st.number_input("Valor a Cadastrar")
                    if st.button("Salvar Valor"):
                        try:
                            supabase.table("fluxo_caixa").insert({"Valor": fluxo_caixa}).execute()
                            st.success("Valor Cadastrado com Sucesso no Supabase!")
                        except Exception as e:
                            st.error(f"Erro: {e}")

                case "Contas a Pagar":
                    st.subheader("Cadastrar Conta a Pagar")
                    try:
                        df_recebedor = pd.DataFrame(supabase.table("fornecedor").select("*").execute().data)
                        forn_lista = df_recebedor["Nome Fornecedor"].tolist() if not df_recebedor.empty else []

                        nota_fiscal = st.text_input("N° Nota Fiscal")
                        recebedor = st.selectbox("Fornecedor", forn_lista)
                        valor = st.number_input("Valor", min_value=0.0, step=0.01)
                        vencimento = st.date_input("Data de Vencimento")
                        n_faturas = st.text_input("Quantidade de Faturas")

                        if st.button("Salvar Fatura"):
                            supabase.table("contas_a_pagar").insert({
                                "NF": nota_fiscal,
                                "Fornecedor": recebedor,
                                "Valor": valor,
                                "Vencimento": str(vencimento),
                                "QTD Faturas": n_faturas,
                                "Status": "Aberto"
                            }).execute()
                            st.success("Fatura salva com sucesso no Supabase!")

                        df_pagar = pd.DataFrame(supabase.table("contas_a_pagar").select("*").execute().data)
                        if not df_pagar.empty:
                            st.subheader("Faturas em Aberto")
                            faturas_abertas = df_pagar[df_pagar["Status"] == "Aberto"]
                            for i, row in faturas_abertas.iterrows():
                                st.write(f"NF: {row['NF']} | Fornecedor: {row['Fornecedor']} | Valor: R$ {row['Valor']:.2f} | Vencimento: {row['Vencimento']}")
                                if st.button(f"Marcar como Paga - NF {row['NF']}", key=f"pagar_{row['NF']}_{i}"):
                                    supabase.table("contas_a_pagar").update({"Status": "Pago"}).eq("NF", row["NF"]).execute()
                                    st.success(f"Fatura {row['NF']} marcada como paga!")
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Erro em Contas a Pagar: {e}")

                case "Contas a Receber":
                    st.subheader("Cadastrar Conta a Receber")
                    try:
                        df_cliente = pd.DataFrame(supabase.table("fornecedor").select("*").execute().data)
                        cli_lista = df_cliente["Nome Fornecedor"].tolist() if not df_cliente.empty else []

                        contrato = st.text_input("N° Contrato")
                        cliente = st.selectbox("Cliente", cli_lista)
                        valor = st.number_input("Valor", min_value=0.0, step=0.01)
                        vencimento = st.date_input("Data de Vencimento")
                        n_faturas = st.text_input("Quantidade de Faturas")

                        if st.button("Salvar Fatura Receber"):
                            supabase.table("contas_a_receber").insert({
                                "Contrato": contrato,
                                "Cliente": cliente,
                                "Valor": valor,
                                "Vencimento": str(vencimento),
                                "QTD Faturas": n_faturas,
                                "Status": "Aberto"
                            }).execute()
                            st.success("Fatura salva com sucesso no Supabase!")

                        df_receber = pd.DataFrame(supabase.table("contas_a_receber").select("*").execute().data)
                        if not df_receber.empty:
                            st.subheader("Faturas em Aberto")
                            faturas_abertas = df_receber[df_receber["Status"] == "Aberto"]
                            for i, row in faturas_abertas.iterrows():
                                st.write(f"Contrato: {row['Contrato']} | Cliente: {row['Cliente']} | Valor: R$ {row['Valor']:.2f} | Vencimento: {row['Vencimento']}")
                                if st.button(f"Marcar como Recebida - Contrato {row['Contrato']}", key=f"receber_{row['Contrato']}_{i}"):
                                    supabase.table("contas_a_receber").update({"Status": "Recebido"}).eq("Contrato", row["Contrato"]).execute()
                                    st.success(f"Fatura do contrato {row['Contrato']} marcada como recebida!")
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Erro em Contas a Receber: {e}")

                case "Relatórios Gerenciais":
                    st.write("Relatórios Gerenciais")
                     
        case "IA":  
            st.subheader("ATLAS IA")
            if "lista_mensagem" not in st.session_state: 
                st.session_state["lista_mensagem"] = []

            for mensagem in st.session_state["lista_mensagem"]:
                st.chat_message(mensagem["role"]).write(mensagem["content"])

            texto_user = st.chat_input("Digite Sua Mensagem")

            if texto_user:
                st.chat_message("user").write(texto_user)
                st.session_state["lista_mensagem"].append({"role": "user", "content": texto_user})

                mensagens = []
                for msg in st.session_state["lista_mensagem"]:
                    mensagens.append({"role": msg["role"],"parts": [{"text": msg["content"]}]})

                resposta_ia = client.models.generate_content(model=modelo, contents=mensagens)
                texto_resposta_ia = resposta_ia.text

                st.chat_message("assistant").write(texto_resposta_ia)
                st.session_state["lista_mensagem"].append({"role": "assistant", "content": texto_resposta_ia})

        case "Contratos":
            escolha_contratos = st.radio("Escolha uma opção:", ["Cadastro de Projeto", "Emissão de Contratos", "Controle de Contratos", "Gestão de Contratos"], horizontal=True)
            match escolha_contratos:
                case "Cadastro de Projeto":
                    st.write("Cadastro de Projeto")
                    nome_projeto = st.text_input("Nome do Projeto")
                    n_projeto = st.text_input("Número do Projeto")
                    valor_projeto = st.number_input("Valor previsto")
                    if st.button("Salvar Projeto"):
                        try:
                            supabase.table("projeto").insert({
                                "Descrição": nome_projeto,
                                "Número Projeto": n_projeto,
                                "Valor": valor_projeto
                            }).execute()
                            st.success("Projeto Salvo com Sucesso no Supabase!")
                        except Exception as e:
                            st.error(f"Erro ao salvar projeto: {e}")        

                case "Emissão de Contratos":
                    try:
                        df_contrato_projeto = pd.DataFrame(supabase.table("projeto").select("*").execute().data)
                        df_fornecedor_contrato = pd.DataFrame(supabase.table("fornecedor").select("*").execute().data)

                        proj_lista = df_contrato_projeto["Descrição"].tolist() if not df_contrato_projeto.empty else []
                        forn_lista = df_fornecedor_contrato["Nome Fornecedor"].tolist() if not df_fornecedor_contrato.empty else []

                        contrato_projeto = st.selectbox("Projeto", proj_lista)
                        empresa_contratante = st.selectbox("Empresa Contratante", ["DigiEvo Tech System"])
                        cnpj_empresa_contratante = st.selectbox("CNPJ Contratante", ["11.111.111/1111-11"])
                        contrato_fornecedor = st.selectbox("Escolha o Fornecedor", forn_lista)
                        
                        cnpj_forn = ""
                        if not df_fornecedor_contrato.empty and contrato_fornecedor:
                            match_f = df_fornecedor_contrato[df_fornecedor_contrato["Nome Fornecedor"] == contrato_fornecedor]
                            if not match_f.empty and "CNPJ" in match_f.columns:
                                cnpj_forn = match_f.iloc[0]["CNPJ"]

                        cnpj_empresa_fornecedor = st.text_input("CNPJ Fornecedor", value=cnpj_forn)
                        contrato_objeto = st.text_area("Objeto do Contrato")
                        valor_contrato = st.number_input("Valor Contrato")
                        contrato_inicio = st.date_input("Data de Inicio")
                        contrato_fim = st.date_input("Data de Conclusão")

                        if st.button("Salvar Contrato"):
                            supabase.table("contrato").insert({
                                "Empresa Contratante": empresa_contratante,
                                "CNPJ Contratante": cnpj_empresa_contratante,
                                "Fornecedor": contrato_fornecedor,
                                "CNPJ Fornecedor": cnpj_empresa_fornecedor,
                                "Objeto": contrato_objeto,
                                "Valor": valor_contrato,
                                "Data Inicio": str(contrato_inicio),
                                "Data Fim": str(contrato_fim),
                                "Projeto": contrato_projeto
                             }).execute()
                            st.success("Contrato Salvo com Sucesso no Supabase!")

                        if st.button("Emitir Contrato PDF"):
                            res_c = supabase.table("contrato").select("*").order("id", desc=True).limit(1).execute()
                            if res_c.data:
                                contrato_pdf = res_c.data[0]
                                c = canvas.Canvas("contrato.pdf", pagesize=A4)
                                largura, altura = A4

                                c.setFont("Helvetica-Bold", 16)
                                c.drawCentredString(largura/2, altura - 50, "CONTRATO DE PRESTAÇÃO DE SERVIÇOS")

                                c.setFont("Helvetica", 12)
                                linha = altura - 100
                                espaco = 20

                                c.drawString(50, linha, f"Projeto: {contrato_pdf.get('Projeto', '')}"); linha -= espaco
                                c.drawString(50, linha, f"Empresa Contratante: {contrato_pdf.get('Empresa Contratante', '')}"); linha -= espaco
                                c.drawString(50, linha, f"CNPJ Contratante: {contrato_pdf.get('CNPJ Contratante', '')}"); linha -= espaco
                                c.drawString(50, linha, f"Fornecedor: {contrato_pdf.get('Fornecedor', '')}"); linha -= espaco
                                c.drawString(50, linha, f"CNPJ Fornecedor: {contrato_pdf.get('CNPJ Fornecedor', '')}"); linha -= espaco
                                c.drawString(50, linha, f"Objeto: {contrato_pdf.get('Objeto', '')}"); linha -= espaco
                                c.drawString(50, linha, f"Valor: R$ {contrato_pdf.get('Valor', 0):.2f}"); linha -= espaco
                                c.drawString(50, linha, f"Data de Início: {contrato_pdf.get('Data Inicio', '')}"); linha -= espaco
                                c.drawString(50, linha, f"Data de Conclusão: {contrato_pdf.get('Data Fim', '')}"); linha -= espaco

                                linha -= 60
                                c.drawString(50, linha, "________________________________________"); linha -= espaco
                                c.drawString(50, linha, "Assinatura da Empresa Contratante")

                                linha -= 60
                                c.drawString(50, linha, "________________________________________"); linha -= espaco
                                c.drawString(50, linha, "Assinatura do Fornecedor")
                                c.save()
                                st.success("Contrato emitido em PDF com sucesso!")
                            else:
                                st.error("Nenhum contrato encontrado no banco.")
                    except Exception as e:
                        st.error(f"Erro nos contratos: {e}")

        case "Desconectar": 
            st.session_state["logado"] = False  
            st.rerun()