import streamlit as st
import pandas as pd
import os
from PIL import Image
import google.genai as genai
import base64
import numpy as np
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image as RLImage, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from supabase import create_client, Client

# Configuração do Supabase
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

st.title("Capsule Sys - Multiempresa")

def tela_login():
    st.title("Login / Seleção de Empresa")
    
    # Buscar lista de empresas cadastradas para selecionar o tenant
    try:
        res_emp = supabase.table("clientes_empresas").select("*").execute()
        df_emp = pd.DataFrame(res_emp.data if res_emp.data else [])
        empresas_lista = df_emp["Nome Empresa"].tolist() if not df_emp.empty and "Nome Empresa" in df_emp.columns else ["Matriz Padrão"]
    except Exception:
        empresas_lista = ["Matriz Padrão"]

    empresa_selecionada = st.selectbox("Empresa / Cliente", empresas_lista)
    usuario = st.text_input("Usuário", value="admin")
    senha = st.text_input("Senha", type="password", value="1234")

    if st.button("Entrar"):
        st.session_state["logado"] = True
        st.session_state["usuario"] = usuario if usuario else "admin"
        st.session_state["empresa_ativa"] = empresa_selecionada
        
        # Buscar permissões do usuário no banco se existir
        try:
            res_u = supabase.table("usuarios").select("*").eq("Usuario", usuario).eq("Empresa", empresa_selecionada).execute()
            if res_u.data:
                st.session_state["permissoes"] = res_u.data[0].get("ModulosPermitidos", "").split(",")
            else:
                st.session_state["permissoes"] = ["Gráficos Gerenciais", "Cadastros", "Almox", "Compras", "Gerencial", "IA", "Contratos"]
        except Exception:
            st.session_state["permissoes"] = ["Gráficos Gerenciais", "Cadastros", "Almox", "Compras", "Gerencial", "IA", "Contratos"]

        st.rerun()

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
else:
    empresa_atual = st.session_state.get("empresa_ativa", "Matriz Padrão")
    st.sidebar.markdown(f"🏢 **Empresa:** `{empresa_atual}`")
    
    # Módulos disponíveis filtrados pelas permissões do usuário
    todos_modulos = ["Gráficos Gerenciais", "Cadastros", "Almox", "Compras", "Gerencial", "IA", "Contratos", "Gestão Empresas", "Desconectar"]
    permissoes_usuario = st.session_state.get("permissoes", todos_modulos)
    
    modulos_permitidos = [m for m in todos_modulos if m in permissoes_usuario or m in ["Desconectar", "Gestão Empresas"]]

    menu = st.sidebar.radio("Ferramentas", modulos_permitidos)

    match menu:
        case "Gestão Empresas":
            st.write("Cadastro de Clientes / Empresas (Multi-tenancy)")
            with st.form("form_cliente_empresa"):
                nome_empresa = st.text_input("Nome da Empresa / Cliente")
                cnpj_emp = st.text_input("CNPJ da Empresa")
                plano = st.selectbox("Plano", ["Básico", "Profissional", "Enterprise"])
                submit_emp = st.form_submit_button("Salvar Empresa")
                if submit_emp:
                    try:
                        supabase.table("clientes_empresas").insert({
                            "Nome Empresa": nome_empresa,
                            "CNPJ": cnpj_empj if 'cnpj_empj' in locals() else cnpj_emp,
                            "Plano": plano,
                            "Status": "Ativo"
                        }).execute()
                        st.success("Empresa cadastrada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar empresa: {e}")

            try:
                res_cli = supabase.table("clientes_empresas").select("*").execute()
                df_cli = pd.DataFrame(res_cli.data if res_cli.data else [])
                if not df_cli.empty:
                    st.subheader("Empresas Cadastradas")
                    st.dataframe(df_cli, use_container_width=True)
            except Exception:
                pass

        case "Gráficos Gerenciais":
            try:
                res_c = supabase.table("fluxo_caixa").select("*").eq("empresa_id", empresa_atual).execute()
                df_caixa = pd.DataFrame(res_c.data if res_c.data else [])
                if not df_caixa.empty and "Valor" in df_caixa.columns:
                    df_caixa["Valor"] = pd.to_numeric(df_caixa["Valor"], errors="coerce").fillna(0)
                    total_caixa = df_caixa["Valor"].sum()
                    st.metric(label="Fluxo de Caixa", value=f"R$ {total_caixa:,.2f}") 
                else:
                    st.metric(label="Fluxo de Caixa", value="R$ 0,00")
            except Exception:
                st.metric(label="Fluxo de Caixa", value="R$ 0,00")

            try:
                res_cp = supabase.table("contas_a_pagar").select("*").eq("empresa_id", empresa_atual).execute()
                df_contasp = pd.DataFrame(res_cp.data if res_cp.data else [])
                if not df_contasp.empty and "Valor" in df_contasp.columns and "Status" in df_contasp.columns:
                    df_contasp["Valor"] = pd.to_numeric(df_contasp["Valor"], errors="coerce").fillna(0)
                    df_abertas = df_contasp[df_contasp["Status"] == "Aberto"]
                    total_contasp = df_abertas["Valor"].sum()
                    st.metric(label="Contas a Pagar (Abertas)", value=f"R$ {total_contasp:,.2f}")
                    if not df_abertas.empty and "Fornecedor" in df_abertas.columns:
                        st.bar_chart(df_abertas.groupby("Fornecedor")["Valor"].sum())
                else:
                    st.metric(label="Contas a Pagar (Abertas)", value="R$ 0,00")
            except Exception:
                st.metric(label="Contas a Pagar (Abertas)", value="R$ 0,00")
                
        case "Cadastros":
            cadastro_opcao = st.radio("Escolha uma Opção:", ["Cadastro de Usuário", "Cadastro de Fornecedor", "Cadastro de Produto", "Cadastro Filial"], horizontal=True)
            match cadastro_opcao:
                case "Cadastro de Usuário":    
                    st.write("Cadastro de Usuário e Permissões")
                    with st.form("form_usuario"):
                        usuario = st.text_input("Usuário")
                        email = st.text_input("E-mail")
                        senha = st.text_input("Senha", type="password")
                        
                        st.write("Permissões de Acesso aos Módulos:")
                        p_graficos = st.checkbox("Gráficos Gerenciais", value=True)
                        p_cadastros = st.checkbox("Cadastros", value=True)
                        p_almox = st.checkbox("Almoxarifado", value=True)
                        p_compras = st.checkbox("Compras", value=True)
                        p_gerencial = st.checkbox("Gerencial (Financeiro)", value=True)
                        p_ia = st.checkbox("ATLAS IA", value=True)
                        p_contratos = st.checkbox("Contratos", value=True)

                        submitted = st.form_submit_button("Salvar Usuário")
                        if submitted:
                            if usuario and email and senha:
                                modulos_escolhidos = []
                                if p_graficos: modulos_escolhidos.append("Gráficos Gerenciais")
                                if p_cadastros: modulos_escolhidos.append("Cadastros")
                                if p_almox: modulos_escolhidos.append("Almox")
                                if p_compras: modulos_escolhidos.append("Compras")
                                if p_gerencial: modulos_escolhidos.append("Gerencial")
                                if p_ia: modulos_escolhidos.append("IA")
                                if p_contratos: modulos_escolhidos.append("Contratos")

                                try:
                                    supabase.table("usuarios").insert({
                                        "Usuario": usuario,
                                        "E-mail": email,
                                        "Senha": senha,
                                        "Empresa": empresa_atual,
                                        "ModulosPermitidos": ",".join(modulos_escolhidos)
                                    }).execute()
                                    st.success("Usuário e permissões salvos com sucesso!")
                                except Exception as e:
                                    st.error(f"Erro ao salvar usuário: {e}")
                            else:
                                st.warning("Preencha todos os campos obrigatórios.")

                case "Cadastro de Fornecedor":
                    st.write("Cadastro de Fornecedor")
                    with st.form("form_fornecedor"):
                        nome_fornecedor = st.text_input("Razão Social")
                        email_fornecedor = st.text_input("E-mail")
                        cnpj_fornecedor = st.text_input("CNPJ")
                        contato_fornecedor = st.text_input("Contato")
                        submitted = st.form_submit_button("Salvar Fornecedor")
                        if submitted:
                            try:
                                supabase.table("fornecedor").insert({
                                    "Nome Fornecedor": nome_fornecedor,
                                    "E-mail Fornecedor": email_fornecedor,
                                    "CNPJ": cnpj_fornecedor,
                                    "Contato Fornecedor": contato_fornecedor,
                                    "empresa_id": empresa_atual
                                }).execute()
                                st.success("Fornecedor Cadastrado com Sucesso!")
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
                        res_f = supabase.table("filial").select("*").eq("empresa_id", empresa_atual).execute()
                        df_fil = pd.DataFrame(res_f.data if res_f.data else [])
                        opcoes_filiais = ["Todas"] + (df_fil["Nome"].tolist() if not df_fil.empty and "Nome" in df_fil.columns else [])
                    except Exception:
                        opcoes_filiais = ["Todas"]

                    filial_escolhida = st.selectbox("Filial", opcoes_filiais)

                    if st.button("Salvar Cadastro"):
                        try:
                            res_prod = supabase.table("produto").select("Codigo").eq("empresa_id", empresa_atual).order("Codigo", desc=True).limit(1).execute()
                            dados_ult = res_prod.data
                            novo_codigo = (int(dados_ult[0]["Codigo"]) + 1) if dados_ult and dados_ult[0].get("Codigo") is not None else 1
                        except Exception:
                            novo_codigo = 1

                        lista_produtos = []
                        if filial_escolhida == "Todas" and not df_fil.empty and "Nome" in df_fil.columns:
                            for nome_filial in df_fil["Nome"].tolist():
                                lista_produtos.append({
                                    "Codigo": novo_codigo,
                                    "Descrição Produto": descricao,
                                    "ean_produto": ean_produto,
                                    "Preço Produto": float(preco_produto),
                                    "Categoria": categoria_produto,
                                    "Sub-Categoria": subcategoria_produto,
                                    "Quantidade Produto": int(quantidade_produto),
                                    "Filial": str(nome_filial),
                                    "empresa_id": empresa_atual
                                })
                        else:
                            lista_produtos.append({
                                "Codigo": novo_codigo,
                                "Descrição Produto": descricao,
                                "ean_produto": ean_produto,
                                "Preço Produto": float(preco_produto),
                                "Categoria": categoria_produto,
                                "Sub-Categoria": subcategoria_produto,
                                "Quantidade Produto": int(quantidade_produto),
                                "Filial": str(filial_escolhida),
                                "empresa_id": empresa_atual
                            })

                        try:
                            supabase.table("produto").insert(lista_produtos).execute()
                            st.success(f"Produto código {novo_codigo} cadastrado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao salvar produto: {e}")

                case "Cadastro Filial":
                    st.write("Cadastro de Filial")
                    with st.form("form_filial"):
                        nome = st.text_input("Descrição Filial")
                        cnpj = st.text_input("CNPJ")
                        endereco = st.text_input("Endereço")
                        codigo = st.text_input("Código Filial")
                        submitted = st.form_submit_button("Salvar Cadastro")
                        if submitted:
                            try:
                                supabase.table("filial").insert({
                                    "Nome": nome,
                                    "CNPJ": cnpj,
                                    "Endereço": endereco,
                                    "Código": codigo,
                                    "empresa_id": empresa_atual
                                }).execute()
                                st.success("Filial Cadastrada com Sucesso!")
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
                        res = supabase.table("produto").select("*").eq("empresa_id", empresa_atual).execute()
                        painel_estoque = pd.DataFrame(res.data if res.data else [])
                        if not painel_estoque.empty:
                            st.dataframe(painel_estoque, use_container_width=True)
                        else:
                            st.info("Nenhum produto cadastrado.")
                    except Exception as e:
                        st.error(f"Erro ao carregar estoque: {e}")

                case "Requisição de Compras":
                    st.write("Requisição de Compras")
                    try:
                        res_p = supabase.table("produto").select("*").eq("empresa_id", empresa_atual).execute()
                        res_f = supabase.table("filial").select("*").eq("empresa_id", empresa_atual).execute()
                        res_proj = supabase.table("projeto").select("*").eq("empresa_id", empresa_atual).execute()

                        df_produtos = pd.DataFrame(res_p.data if res_p.data else [])
                        df_filial = pd.DataFrame(res_f.data if res_f.data else [])
                        df_nome_projeto = pd.DataFrame(res_proj.data if res_proj.data else [])

                        prod_lista = df_produtos["Descrição Produto"].unique().tolist() if not df_produtos.empty and "Descrição Produto" in df_produtos.columns else []
                        fil_lista = df_filial["Nome"].unique().tolist() if not df_filial.empty and "Nome" in df_filial.columns else []
                        proj_desc = df_nome_projeto["Descrição"].unique().tolist() if not df_nome_projeto.empty and "Descrição" in df_nome_projeto.columns else []
                        proj_num = df_nome_projeto["Número Projeto"].unique().tolist() if not df_nome_projeto.empty and "Número Projeto" in df_nome_projeto.columns else []

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
                                "Quantidade": int(quantidade),
                                "Filial Requisitante": filial,
                                "Nome Projeto": nome_projeto, 
                                "N° Projeto": str(n_projeto),
                                "empresa_id": empresa_atual
                            }
                            st.session_state.item_requisicao.append(item)
                            st.success(f"Produto {produto_escolhido} adicionado (Qtd: {quantidade})")

                        if len(st.session_state.item_requisicao) > 0:
                            st.subheader("Itens adicionados à requisição")
                            st.table(pd.DataFrame(st.session_state.item_requisicao))

                        if st.button("Salvar Requisição"):
                            try:
                                res_req = supabase.table("requisicoes").select("Codigo").eq("empresa_id", empresa_atual).order("Codigo", desc=True).limit(1).execute()
                                ult_req = res_req.data
                                novo_codigo = (int(ult_req[0]["Codigo"]) + 1) if ult_req and ult_req[0].get("Codigo") is not None else 1
                            except Exception:
                                novo_codigo = 1

                            nova_requisicao = [
                                {"Codigo": novo_codigo, **item} for item in st.session_state.item_requisicao
                            ]
                            supabase.table("requisicoes").insert(nova_requisicao).execute()
                            st.success(f"Pedido de Compra {novo_codigo} salvo com sucesso!")

                        if st.button("Limpar Lista"):
                            st.session_state.item_requisicao = []
                            st.warning("Lista de itens foi limpa.")
                    except Exception as e:
                        st.error(f"Erro na requisição: {e}")

                case "Ajuste de Estoque":
                    st.write("Ajuste de Estoque")
                    try:
                        res_p = supabase.table("produto").select("*").eq("empresa_id", empresa_atual).execute()
                        res_f = supabase.table("filial").select("*").eq("empresa_id", empresa_atual).execute()

                        df_produtos = pd.DataFrame(res_p.data if res_p.data else [])
                        df_filial = pd.DataFrame(res_f.data if res_f.data else [])

                        prod_lista = df_produtos["Descrição Produto"].tolist() if not df_produtos.empty and "Descrição Produto" in df_produtos.columns else []
                        fil_lista = df_filial["Nome"].tolist() if not df_filial.empty and "Nome" in df_filial.columns else []

                        ajuste_produto = st.selectbox("Produto", prod_lista)
                        ajuste_quantidade = st.number_input("Nova Quantidade", min_value=0)
                        ajuste_motivos = st.selectbox("Motivo Ajuste", ["Avaria", "Inventário", "Consumo"])
                        ajuste_filial = st.selectbox("Filial Ajuste", fil_lista)         

                        if st.button("Salvar Ajuste"):
                            supabase.table("ajuste_estoque").insert({
                                "Produto": ajuste_produto,
                                "Quantidade": int(ajuste_quantidade),
                                "Motivo Ajuste": ajuste_motivos,
                                "Filial": ajuste_filial,
                                "empresa_id": empresa_atual
                            }).execute()

                            supabase.table("produto").update({"Quantidade Produto": int(ajuste_quantidade)}).eq("Descrição Produto", ajuste_produto).eq("Filial", ajuste_filial).eq("empresa_id", empresa_atual).execute()
                            st.success("Ajuste Realizado com Sucesso!")
                    except Exception as e:
                        st.error(f"Erro no ajuste de estoque: {e}")

                case "Recebimento":
                    st.write("Recebimento de Mercadorias")
                    try:
                        res_v = supabase.table("vencedores").select("*").eq("empresa_id", empresa_atual).execute()
                        df_pedido = pd.DataFrame(res_v.data if res_v.data else [])
                        if not df_pedido.empty and "NumeroPedido" in df_pedido.columns and "Fornecedor" in df_pedido.columns:
                            df_pedido["PedidoLabel"] = df_pedido["NumeroPedido"].astype(str) + " - " + df_pedido["Fornecedor"].astype(str)
                            pedido = st.selectbox("Selecione o Pedido para Recebimento", df_pedido["PedidoLabel"].unique().tolist())

                            numero_pedido, fornecedor = str(pedido).split(" - ", 1)
                            df_itens_pedido = df_pedido[
                                (df_pedido["NumeroPedido"].astype(str) == numero_pedido) &
                                (df_pedido["Fornecedor"].astype(str) == fornecedor)
                            ]

                            st.write("Itens do Pedido:")
                            st.table(df_itens_pedido[["Produto", "Preço Cotado"]])

                            res_p = supabase.table("produto").select("*").eq("empresa_id", empresa_atual).execute()
                            df_produto = pd.DataFrame(res_p.data if res_p.data else [])
                            filiais = df_produto["Filial"].unique().tolist() if not df_produto.empty and "Filial" in df_produto.columns else []
                            filial_escolhida = st.selectbox("Selecione a Filial de Entrada", filiais)

                            recebimentos = {}
                            for _, row in df_itens_pedido.iterrows():
                                qtd_recebida = st.number_input(
                                    f"Quantidade recebida de {row['Produto']} na filial {filial_escolhida}",
                                    min_value=0,
                                    step=1
                                )
                                recebimentos[row["Produto"]] = int(qtd_recebida)

                            if st.button("Confirmar Recebimento"):
                                for produto, qtd in recebimentos.items():
                                    if qtd > 0:
                                        res_q = supabase.table("produto").select("id, Quantidade Produto").eq("Descrição Produto", produto).eq("Filial", filial_escolhida).eq("empresa_id", empresa_atual).execute()
                                        if res_q.data:
                                            row_p = res_q.data[0]
                                            qtd_atual = int(row_p.get("Quantidade Produto", 0) or 0)
                                            novo_total = qtd_atual + int(qtd)
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
                        res_r = supabase.table("requisicoes").select("*").eq("empresa_id", empresa_atual).execute()
                        res_f = supabase.table("fornecedor").select("*").eq("empresa_id", empresa_atual).execute()

                        df_req_gestao = pd.DataFrame(res_r.data if res_r.data else [])
                        df_req_fornecedor = pd.DataFrame(res_f.data if res_f.data else [])

                        if not df_req_gestao.empty and not df_req_fornecedor.empty and "Codigo" in df_req_gestao.columns and "Nome Fornecedor" in df_req_fornecedor.columns:
                            df_req_gestao["Codigo"] = df_req_gestao["Codigo"].fillna(0).astype(str)
                            df_req_gestao["Nome Projeto"] = df_req_gestao.get("Nome Projeto", "").fillna("").astype(str)
                            df_req_gestao["Requisicao_Label"] = df_req_gestao["Codigo"] + " - " + df_req_gestao["Nome Projeto"]

                            requisicao_compra = st.selectbox("Requisição", df_req_gestao["Requisicao_Label"].unique().tolist())
                            req_fornecedor = st.selectbox("Escolha o Fornecedor", df_req_fornecedor["Nome Fornecedor"])
                            codigo_selecionado = str(requisicao_compra).split(" - ")[0]
                            data_emissao = st.date_input("Data de Emissão do Pedido")
                            data_recebimento = st.date_input("Data de Recebimento do Pedido")

                            df_filtrada = df_req_gestao[df_req_gestao["Codigo"] == codigo_selecionado].copy()
                            df_filtrada["Preço Cotado"] = 0.0
                            df_editado = st.data_editor(df_filtrada)

                            if st.button("Salvar Cotação"):
                                for col_remover in ["Requisicao_Label", "id", "empresa_id"]:
                                    if col_remover in df_editado.columns:
                                        df_editado = df_editado.drop(columns=[col_remover])

                                df_editado["Requisição"] = str(requisicao_compra)
                                df_editado["Fornecedor"] = str(req_fornecedor)
                                df_editado["Data Emissão"] = str(data_emissao)
                                df_editado["Data Recebimento"] = str(data_recebimento)
                                df_editado["empresa_id"] = empresa_atual
                                
                                dados_inserir = df_editado.to_dict(orient="records")
                                supabase.table("cotacoes").insert(dados_inserir).execute()
                                st.success("Cotação salva com sucesso!")
                        else:
                            st.info("Cadastre requisições e fornecedores primeiro.")
                    except Exception as e:
                        st.error(f"Erro na gestão de compras: {e}")

                case "Definição de Vencedores":
                    st.write("Definição de Vencedores")
                    try:
                        res_c = supabase.table("cotacoes").select("*").eq("empresa_id", empresa_atual).execute()
                        df = pd.DataFrame(res_c.data if res_c.data else [])
                        if not df.empty and "Codigo" in df.columns:
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
                                        f"{fornecedor} - R$ {float(valor or 0):.2f}", value=default, key=f"{produto}_{fornecedor}"
                                    )

                            if st.button("Definir Vencedores"):
                                try:
                                    res_v = supabase.table("vencedores").select("NumeroPedido").eq("empresa_id", empresa_atual).order("NumeroPedido", desc=True).limit(1).execute()
                                    ult_v = res_v.data
                                    proximo_numero = (int(ult_v[0]["NumeroPedido"]) + 1) if ult_v and ult_v[0].get("NumeroPedido") is not None else 1
                                except Exception:
                                    proximo_numero = 1

                                selecionados = [
                                    {
                                        "Produto": str(prod),
                                        "Fornecedor": str(forn),
                                        "Preço Cotado": float(tabela.loc[prod, forn]),
                                        "Selecionado": True,
                                        "NumeroPedido": int(proximo_numero),
                                        "empresa_id": empresa_atual
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
                        res_v = supabase.table("vencedores").select("*").eq("empresa_id", empresa_atual).execute()
                        df_pedido = pd.DataFrame(res_v.data if res_v.data else [])
                        if not df_pedido.empty and "NumeroPedido" in df_pedido.columns and "Fornecedor" in df_pedido.columns:
                            df_pedido["PedidoLabel"] = df_pedido["NumeroPedido"].astype(str) + " - " + df_pedido["Fornecedor"].astype(str)
                            pedido = st.selectbox("Selecione um Pedido de Compra", df_pedido["PedidoLabel"].unique().tolist())

                            numero_pedido, fornecedor = str(pedido).split(" - ", 1)

                            buffer = io.BytesIO()
                            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
                            elementos = []

                            if os.path.exists("capsuleSys.png"):
                                logo = RLImage("capsuleSys.png", width=120, height=50)
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
                                dados.append([row["Produto"], row["Fornecedor"], f"R$ {float(row['Preço Cotado'] or 0):.2f}"])

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
                            supabase.table("fluxo_caixa").insert({
                                "Valor": float(fluxo_caixa),
                                "empresa_id": empresa_atual
                            }).execute()
                            st.success("Valor Cadastrado com Sucesso!")
                        except Exception as e:
                            st.error(f"Erro: {e}")

                case "Contas a Pagar":
                    st.subheader("Cadastrar Conta a Pagar")
                    try:
                        res_f = supabase.table("fornecedor").select("*").eq("empresa_id", empresa_atual).execute()
                        df_recebedor = pd.DataFrame(res_f.data if res_f.data else [])
                        forn_lista = df_recebedor["Nome Fornecedor"].tolist() if not df_recebedor.empty and "Nome Fornecedor" in df_recebedor.columns else []

                        nota_fiscal = st.text_input("N° Nota Fiscal")
                        recebedor = st.selectbox("Fornecedor", forn_lista)
                        valor = st.number_input("Valor", min_value=0.0, step=0.01)
                        vencimento = st.date_input("Data de Vencimento")
                        n_faturas = st.text_input("Quantidade de Faturas")

                        if st.button("Salvar Fatura"):
                            supabase.table("contas_a_pagar").insert({
                                "NF": str(nota_fiscal),
                                "Fornecedor": str(recebedor),
                                "Valor": float(valor),
                                "Vencimento": str(vencimento),
                                "QTD Faturas": str(n_faturas),
                                "Status": "Aberto",
                                "empresa_id": empresa_atual
                            }).execute()
                            st.success("Fatura salva com sucesso!")

                        res_cp = supabase.table("contas_a_pagar").select("*").eq("empresa_id", empresa_atual).execute()
                        df_pagar = pd.DataFrame(res_cp.data if res_cp.data else [])
                        if not df_pagar.empty and "Status" in df_pagar.columns:
                            st.subheader("Faturas em Aberto")
                            faturas_abertas = df_pagar[df_pagar["Status"] == "Aberto"]
                            for i, row in faturas_abertas.iterrows():
                                st.write(f"NF: {row.get('NF', '')} | Fornecedor: {row.get('Fornecedor', '')} | Valor: R$ {float(row.get('Valor', 0) or 0):,.2f} | Vencimento: {row.get('Vencimento', '')}")
                                if st.button(f"Marcar como Paga - NF {row.get('NF', '')}", key=f"pagar_{row.get('NF', '')}_{i}"):
                                    supabase.table("contas_a_pagar").update({"Status": "Pago"}).eq("NF", row["NF"]).eq("empresa_id", empresa_atual).execute()
                                    st.success(f"Fatura {row.get('NF', '')} marcada como paga!")
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Erro em Contas a Pagar: {e}")

                case "Contas a Receber":
                    st.subheader("Cadastrar Conta a Receber")
                    try:
                        res_f = supabase.table("fornecedor").select("*").eq("empresa_id", empresa_atual).execute()
                        df_cliente = pd.DataFrame(res_f.data if res_f.data else [])
                        cli_lista = df_cliente["Nome Fornecedor"].tolist() if not df_cliente.empty and "Nome Fornecedor" in df_cliente.columns else []

                        contrato = st.text_input("N° Contrato")
                        cliente = st.selectbox("Cliente", cli_lista)
                        valor = st.number_input("Valor", min_value=0.0, step=0.01)
                        vencimento = st.date_input("Data de Vencimento")
                        n_faturas = st.text_input("Quantidade de Faturas")

                        if st.button("Salvar Fatura Receber"):
                            supabase.table("contas_a_receber").insert({
                                "Contrato": str(contrato),
                                "Cliente": str(cliente),
                                "Valor": float(valor),
                                "Vencimento": str(vencimento),
                                "QTD Faturas": str(n_faturas),
                                "Status": "Aberto",
                                "empresa_id": empresa_atual
                            }).execute()
                            st.success("Fatura salva com sucesso!")

                        res_cr = supabase.table("contas_a_receber").select("*").eq("empresa_id", empresa_atual).execute()
                        df_receber = pd.DataFrame(res_cr.data if res_cr.data else [])
                        if not df_receber.empty and "Status" in df_receber.columns:
                            st.subheader("Faturas em Aberto")
                            faturas_abertas = df_receber[df_receber["Status"] == "Aberto"]
                            for i, row in faturas_abertas.iterrows():
                                st.write(f"Contrato: {row.get('Contrato', '')} | Cliente: {row.get('Cliente', '')} | Valor: R$ {float(row.get('Valor', 0) or 0):,.2f} | Vencimento: {row.get('Vencimento', '')}")
                                if st.button(f"Marcar como Recebida - Contrato {row.get('Contrato', '')}", key=f"receber_{row.get('Contrato', '')}_{i}"):
                                    supabase.table("contas_a_receber").update({"Status": "Recebido"}).eq("Contrato", row["Contrato"]).eq("empresa_id", empresa_atual).execute()
                                    st.success(f"Fatura do contrato {row.get('Contrato', '')} marcada como recebida!")
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
                    with st.form("form_projeto"):
                        nome_projeto = st.text_input("Nome do Projeto")
                        n_projeto = st.text_input("Número do Projeto")
                        valor_projeto = st.number_input("Valor previsto")
                        submit = st.form_submit_button("Salvar Projeto")
                        if submit:
                            try:
                                supabase.table("projeto").insert({
                                    "Descrição": nome_projeto,
                                    "Número Projeto": n_projeto,
                                    "Valor": float(valor_projeto),
                                    "empresa_id": empresa_atual
                                }).execute()
                                st.success("Projeto Salvo com Sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao salvar projeto: {e}")        

                case "Emissão de Contratos":
                    try:
                        res_p = supabase.table("projeto").select("*").eq("empresa_id", empresa_atual).execute()
                        res_f = supabase.table("fornecedor").select("*").eq("empresa_id", empresa_atual).execute()

                        df_contrato_projeto = pd.DataFrame(res_p.data if res_p.data else [])
                        df_fornecedor_contrato = pd.DataFrame(res_f.data if res_f.data else [])

                        proj_lista = df_contrato_projeto["Descrição"].tolist() if not df_contrato_projeto.empty and "Descrição" in df_contrato_projeto.columns else []
                        forn_lista = df_fornecedor_contrato["Nome Fornecedor"].tolist() if not df_fornecedor_contrato.empty and "Nome Fornecedor" in df_fornecedor_contrato.columns else []

                        contrato_projeto = st.selectbox("Projeto", proj_lista)
                        empresa_contratante = st.selectbox("Empresa Contratante", ["DigiEvo Tech System"])
                        cnpj_empresa_contratante = st.selectbox("CNPJ Contratante", ["11.111.111/1111-11"])
                        contrato_fornecedor = st.selectbox("Escolha o Fornecedor", forn_lista)
                        
                        cnpj_forn = ""
                        if not df_fornecedor_contrato.empty and contrato_fornecedor and "Nome Fornecedor" in df_fornecedor_contrato.columns:
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
                                "Empresa Contratante": str(empresa_contratante),
                                "CNPJ Contratante": str(cnpj_empresa_contratante),
                                "Fornecedor": str(contrato_fornecedor),
                                "CNPJ Fornecedor": str(cnpj_empresa_fornecedor),
                                "Objeto": str(contrato_objeto),
                                "Valor": float(valor_contrato),
                                "Data Inicio": str(contrato_inicio),
                                "Data Fim": str(contrato_fim),
                                "Projeto": str(contrato_projeto),
                                "empresa_id": empresa_atual
                            }).execute()
                            st.success("Contrato Salvo com Sucesso!")

                        if st.button("Emitir Contrato PDF"):
                            res_c = supabase.table("contrato").select("*").eq("empresa_id", empresa_atual).order("id", desc=True).limit(1).execute()
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
                                c.drawString(50, linha, f"Valor: R$ {float(contrato_pdf.get('Valor', 0) or 0):,.2f}"); linha -= espaco
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
                                st.error("Nenhum contrato encontrado.")
                    except Exception as e:
                        st.error(f"Erro nos contratos: {e}")

        case "Desconectar": 
            st.session_state["logado"] = False  
            st.rerun()