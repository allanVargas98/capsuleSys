import base64
import io
import os
from datetime import date, datetime

import google.genai as genai
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client

# ==========================================
# CONFIGURAÇÃO DE SEGURANÇA E CONEXÃO
# ==========================================
SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL", "https://vhhpetifyuawfiuzdrsu.supabase.co"
)
SUPABASE_KEY = st.secrets.get(
    "SUPABASE_KEY", "sb_publishable_2UpNmtRVpMTMXwYYa_0Kkw_oPc5A2jR"
)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuração Segura do Google Gemini IA
try:
  gemini_key = st.secrets.get("GEMINI_API_KEY", "")
  client = genai.Client(api_key=gemini_key) if gemini_key else None
except Exception:
  client = None

modelo = "models/gemini-3-flash-preview"


# ==========================================
# AUDITORIA E LOGS
# ==========================================
def registrar_log(usuario, empresa, acao, detalhe=""):
  try:
    supabase.table("audit_logs").insert({
        "usuario": usuario,
        "empresa_id": empresa,
        "acao": acao,
        "detalhe": detalhe,
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }).execute()
  except Exception:
    pass


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
    background-size: 18%;
    background-position: right top;
    background-repeat: no-repeat;
}}
[data-testid="stHeader"] {{
    background: rgba(0,0,0,0);
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

st.title("Capsule Sys — ERP de Gestão")


# ==========================================
# GESTÃO DE TENANTS & AUTENTICAÇÃO
# ==========================================
def obter_lista_empresas():
  try:
    res_emp = supabase.table("clientes_empresas").select("*").execute()
    lista = []
    if res_emp.data:
      for item in res_emp.data:
        nome = (
            item.get("Nome Empresa")
            or item.get("nome_empresa")
            or item.get("NomeEmpresa")
        )
        if nome and nome not in lista:
          lista.append(str(nome))
    if "DigiEvo Business LTDA" not in lista:
      lista.insert(0, "DigiEvo Business LTDA")
    return lista
  except Exception:
    return ["DigiEvo Business LTDA"]


def tela_login():
  st.title("Login de Acesso")

  usuario_input = st.text_input("Usuário", value="")
  senha_input = st.text_input("Senha", type="password", value="")

  if st.button("Entrar", type="primary"):
    u_limpo = usuario_input.strip()
    s_limpa = senha_input.strip()

    if not u_limpo or not s_limpa:
      st.warning("Por favor, preencha o usuário e a senha.")
      return

    if u_limpo.lower() == "admin" and s_limpa == "1234":
      st.session_state["logado"] = True
      st.session_state["usuario"] = "admin"
      st.session_state["empresa_ativa"] = "DigiEvo Business LTDA"
      st.session_state["is_master"] = True
      st.session_state["permissoes"] = [
          "Gráficos Gerenciais",
          "Aprovacao Requisicao",
          "Cadastros",
          "Almox",
          "Compras",
          "Gerencial",
          "IA",
          "Contratos",
          "Gestão Empresas",
          "Auditoria",
      ]
      registrar_log(
          "admin",
          "DigiEvo Business LTDA",
          "Login Sucesso",
          "Acesso Master via credencial primária",
      )
      st.rerun()
      return

    try:
      res_u = (
          supabase.table("usuarios")
          .select("*")
          .ilike("Usuario", u_limpo)
          .execute()
      )
      dados_u = res_u.data

      if dados_u:
        login_sucesso = False
        u_info_valido = None

        for u_info in dados_u:
          status_usuario = u_info.get("Status", "Ativo")
          senha_cadastrada = str(u_info.get("Senha", "")).strip()

          if s_limpa == senha_cadastrada:
            if status_usuario == "Inativo":
              st.error(
                  "Este utilizador encontra-se inativo. Contacte o"
                  " administrador."
              )
              return
            login_sucesso = True
            u_info_valido = u_info
            break

        if login_sucesso and u_info_valido:
          empresa_vinculada = u_info_valido.get(
              "Empresa", "DigiEvo Business LTDA"
          )
          modulos_str = u_info_valido.get("ModulosPermitidos", "")

          st.session_state["logado"] = True
          st.session_state["usuario"] = u_info_valido.get("Usuario")
          st.session_state["empresa_ativa"] = empresa_vinculada
          st.session_state["is_master"] = (
              str(u_info_valido.get("Usuario")).lower() == "admin"
          )
          st.session_state["permissoes"] = (
              [m.strip() for m in modulos_str.split(",")]
              if modulos_str
              else [
                  "Gráficos Gerenciais",
                  "Aprovacao Requisicao",
                  "Cadastros",
                  "Almox",
                  "Compras",
                  "Gerencial",
                  "IA",
                  "Contratos",
              ]
          )

          registrar_log(
              st.session_state["usuario"],
              empresa_vinculada,
              "Login Sucesso",
              "Autenticação via base de dados",
          )
          st.rerun()
        else:
          st.error("Senha incorreta para este usuário.")
      else:
        st.error("Usuário não encontrado no banco de dados.")
    except Exception as e:
      st.error(f"Erro ao autenticar: {e}")


if "logado" not in st.session_state:
  st.session_state["logado"] = False

if not st.session_state["logado"]:
  tela_login()
else:
  usuario_atual = st.session_state.get("usuario", "admin")
  is_master = st.session_state.get("is_master", False)

  st.sidebar.markdown(f"**Usuário:** `{usuario_atual}`")

  if is_master or usuario_atual.lower() == "admin":
    lista_empresas_clientes = obter_lista_empresas()
    empresa_atual = st.sidebar.selectbox(
        "Empresa (Alternar Cliente)",
        lista_empresas_clientes,
        index=(
            lista_empresas_clientes.index(
                st.session_state.get("empresa_ativa", "DigiEvo Business LTDA")
            )
            if st.session_state.get("empresa_ativa") in lista_empresas_clientes
            else 0
        ),
    )
    st.session_state["empresa_ativa"] = empresa_atual
  else:
    empresa_atual = st.session_state.get(
        "empresa_ativa", "DigiEvo Business LTDA"
    )
    st.sidebar.markdown(f"**Empresa:** `{empresa_atual}`")

  todos_modulos = [
      "Gráficos Gerenciais",
      "Aprovacao Requisicao",
      "Cadastros",
      "Almox",
      "Compras",
      "Gerencial",
      "IA",
      "Contratos",
      "Gestão Empresas",
      "Auditoria",
      "Desconectar",
  ]
  permissoes_usuario = st.session_state.get("permissoes", [])

  if is_master or usuario_atual.lower() == "admin":
    modulos_permitidos = todos_modulos
  else:
    modulos_permitidos = [
        m for m in todos_modulos if m in permissoes_usuario or m == "Desconectar"
    ]

  menu = st.sidebar.radio("Navegação ERP", modulos_permitidos)

  # ==========================================
  # LÓGICA DOS MÓDULOS
  # ==========================================
  match menu:
    case "Gráficos Gerenciais":
      st.header(f"Painel Executivo — {empresa_atual}")

      st.subheader("Performance de Suprimentos & Saving por Pedido")
      try:
        res_v = (
            supabase.table("vencedores")
            .select("*")
            .eq("empresa_id", empresa_atual)
            .execute()
        )
        res_c = (
            supabase.table("cotacoes")
            .select("*")
            .eq("empresa_id", empresa_atual)
            .execute()
        )

        df_vencedores = pd.DataFrame(res_v.data if res_v.data else [])
        df_cotacoes = pd.DataFrame(res_c.data if res_c.data else [])

        if not df_vencedores.empty:
          df_vencedores["Preço Cotado"] = pd.to_numeric(
              df_vencedores["Preço Cotado"], errors="coerce"
          ).fillna(0.0)
          df_vencedores["Quantidade"] = pd.to_numeric(
              df_vencedores["Quantidade"], errors="coerce"
          ).fillna(1.0)
          df_vencedores["Total Pago"] = (
              df_vencedores["Preço Cotado"] * df_vencedores["Quantidade"]
          )

          df_vencedores["Preço Referencia"] = df_vencedores["Preço Cotado"]
          if not df_cotacoes.empty and "Produto" in df_cotacoes.columns:
            df_cotacoes["Preço Cotado"] = pd.to_numeric(
                df_cotacoes["Preço Cotado"], errors="coerce"
            ).fillna(0.0)
            map_max = (
                df_cotacoes.groupby("Produto")["Preço Cotado"].max().to_dict()
            )
            for idx, row in df_vencedores.iterrows():
              prod_nome = row["Produto"]
              if (
                  prod_nome in map_max
                  and map_max[prod_nome] > row["Preço Cotado"]
              ):
                df_vencedores.at[idx, "Preço Referencia"] = map_max[prod_nome]

          df_vencedores["Total Referencia"] = (
              df_vencedores["Preço Referencia"] * df_vencedores["Quantidade"]
          )
          df_vencedores["Saving Absoluto"] = (
              df_vencedores["Total Referencia"] - df_vencedores["Total Pago"]
          )

          df_pedido_saving = (
              df_vencedores.groupby("NumeroPedido")[
                  ["Total Referencia", "Total Pago", "Saving Absoluto"]
              ]
              .sum()
              .reset_index()
          )
          df_pedido_saving["% Saving"] = (
              df_pedido_saving["Saving Absoluto"]
              / df_pedido_saving["Total Referencia"]
              * 100
          ).fillna(0.0)

          tot_comprado_geral = df_pedido_saving["Total Pago"].sum()
          tot_ref_geral = df_pedido_saving["Total Referencia"].sum()
          tot_saving_geral = df_pedido_saving["Saving Absoluto"].sum()
          pct_saving_geral = (
              (tot_saving_geral / tot_ref_geral * 100) if tot_ref_geral > 0 else 0.0
          )

          s_col1, s_col2, s_col3 = st.columns(3)
          s_col1.metric(
              "Total Comprado nos Pedidos", f"R$ {tot_comprado_geral:,.2f}"
          )
          s_col2.metric(
              "Valor de Referência (Mapa)", f"R$ {tot_ref_geral:,.2f}"
          )
          s_col3.metric(
              "Saving Total por Pedido",
              f"R$ {tot_saving_geral:,.2f}",
              delta=f"{pct_saving_geral:.2f}% de economia",
          )

          st.markdown("---")
          st.subheader("Detalhamento do Saving por Pedido de Compra")
          st.dataframe(
              df_pedido_saving.style.format({
                  "Total Referencia": "R$ {:,.2f}",
                  "Total Pago": "R$ {:,.2f}",
                  "Saving Absoluto": "R$ {:,.2f}",
                  "% Saving": "{:.2f}%",
              }),
              use_container_width=True,
          )
        else:
          st.info(
              "Nenhum pedido processado para consolidar os indicadores de"
              " saving por pedido."
          )
      except Exception as e:
        st.error(f"Erro ao carregar indicadores de saving: {e}")

      st.divider()

      st.subheader("Alertas de Estoque & Pendências")
      col_a1, col_a2 = st.columns(2)

      with col_a1:
        try:
          res_p = (
              supabase.table("produto")
              .select("*")
              .eq("empresa_id", empresa_atual)
              .execute()
          )
          df_prod_alert = pd.DataFrame(res_p.data if res_p.data else [])
          if (
              not df_prod_alert.empty
              and "Quantidade Produto" in df_prod_alert.columns
          ):
            df_prod_alert["Quantidade Produto"] = pd.to_numeric(
                df_prod_alert["Quantidade Produto"], errors="coerce"
            ).fillna(0)
            baixos = df_prod_alert[df_prod_alert["Quantidade Produto"] <= 5]
            if not baixos.empty:
              st.warning(
                  f"**{len(baixos)} produto(s)** com estoque crítico (≤ 5"
                  " un.):"
              )
              st.dataframe(
                  baixos[["Descrição Produto", "Quantidade Produto", "Filial"]],
                  use_container_width=True,
              )
            else:
              st.success("Estoque em níveis ideais.")
        except Exception:
          pass

      with col_a2:
        try:
          res_cp = (
              supabase.table("contas_a_pagar")
              .select("*")
              .eq("empresa_id", empresa_atual)
              .execute()
          )
          df_cp_alert = pd.DataFrame(res_cp.data if res_cp.data else [])
          if not df_cp_alert.empty and "Status" in df_cp_alert.columns:
            abertas = df_cp_alert[df_cp_alert["Status"] == "Aberto"]
            if not abertas.empty:
              st.error(f"**{len(abertas)} conta(s) a pagar** em aberto.")
              st.dataframe(
                  abertas[["NF", "Fornecedor", "Valor", "Vencimento"]],
                  use_container_width=True,
              )
            else:
              st.success("Nenhuma conta pendente de pagamento.")
        except Exception:
          pass

      st.divider()

      col_m1, col_m2 = st.columns(2)
      with col_m1:
        try:
          res_c = (
              supabase.table("fluxo_caixa")
              .select("*")
              .eq("empresa_id", empresa_atual)
              .execute()
          )
          df_caixa = pd.DataFrame(res_c.data if res_c.data else [])
          if not df_caixa.empty and "Valor" in df_caixa.columns:
            df_caixa["Valor"] = pd.to_numeric(
                df_caixa["Valor"], errors="coerce"
            ).fillna(0)
            total_caixa = df_caixa["Valor"].sum()
            st.metric(
                label="Saldo em Fluxo de Caixa", value=f"R$ {total_caixa:,.2f}"
            )
          else:
            st.metric(label="Saldo em Fluxo de Caixa", value="R$ 0,00")
        except Exception:
          st.metric(label="Saldo em Fluxo de Caixa", value="R$ 0,00")

      with col_m2:
        try:
          res_cp = (
              supabase.table("contas_a_pagar")
              .select("*")
              .eq("empresa_id", empresa_atual)
              .execute()
          )
          df_contasp = pd.DataFrame(res_cp.data if res_cp.data else [])
          if (
              not df_contasp.empty
              and "Valor" in df_contasp.columns
              and "Status" in df_contasp.columns
          ):
            df_contasp["Valor"] = pd.to_numeric(
                df_contasp["Valor"], errors="coerce"
            ).fillna(0)
            df_abertas = df_contasp[df_contasp["Status"] == "Aberto"]
            total_contasp = df_abertas["Valor"].sum()
            st.metric(
                label="Total Contas a Pagar (Abertas)",
                value=f"R$ {total_contasp:,.2f}",
            )
            if not df_abertas.empty and "Fornecedor" in df_abertas.columns:
              st.bar_chart(df_abertas.groupby("Fornecedor")["Valor"].sum())
          else:
            st.metric(
                label="Total Contas a Pagar (Abertas)",
                value=f"R$ {total_contasp:,.2f}",
            )
        except Exception:
          st.metric(label="Total Contas a Pagar (Abertas)", value="R$ 0,00")

    case "Aprovacao Requisicao":
      st.header("Central de Aprovação de Requisições")
      st.caption(
          "Workflow do Gestor/Diretor agrupado por Código de Requisição para"
          " análise e aprovação."
      )
      try:
        res_reqs = (
            supabase.table("requisicoes")
            .select("*")
            .eq("empresa_id", empresa_atual)
            .execute()
        )
        df_reqs = pd.DataFrame(res_reqs.data if res_reqs.data else [])

        if not df_reqs.empty:
          if "Status" not in df_reqs.columns:
            df_reqs["Status"] = "Aprovado"
          df_reqs["Status"] = df_reqs["Status"].fillna("Aguardando Aprovação")

          # Filtrar apenas as pendentes para a seleção agrupada
          pendentes = df_reqs[df_reqs["Status"] == "Aguardando Aprovação"]

          if not pendentes.empty:
            pendentes["Codigo"] = pendentes["Codigo"].fillna(0).astype(str)
            pendentes["Nome Projeto"] = (
                pendentes["Nome Projeto"].fillna("N/D").astype(str)
            )
            pendentes["ReqLabel"] = (
                "Requisição N° "
                + pendentes["Codigo"]
                + " - Obra: "
                + pendentes["Nome Projeto"]
            )

            req_selecionada = st.selectbox(
                "Selecione a Requisição para Análise",
                pendentes["ReqLabel"].unique().tolist(),
            )

            codigo_escolhido = (
                str(req_selecionada)
                .split(" - ")[0]
                .replace("Requisição N° ", "")
                .strip()
            )
            df_itens_req = pendentes[pendentes["Codigo"] == codigo_escolhido]

            st.write(f"**Itens da Requisição N° {codigo_escolhido}:**")
            st.dataframe(
                df_itens_req[[
                    "Produto",
                    "Quantidade",
                    "Filial Requisitante",
                    "Nome Projeto",
                    "N° Projeto",
                ]],
                use_container_width=True,
            )

            col_ap1, col_ap2 = st.columns(2)
            with col_ap1:
              if st.button("Aprovar Requisição Completa", type="primary"):
                for _, row_item in df_itens_req.iterrows():
                  supabase.table("requisicoes").update(
                      {"Status": "Aprovado"}
                  ).eq("id", row_item.get("id")).execute()
                registrar_log(
                    usuario_atual,
                    empresa_atual,
                    "Aprovacao Requisicao",
                    f"Cod: {codigo_escolhido}",
                )
                st.success(
                    f"Requisição N° {codigo_escolhido} aprovada com sucesso!"
                )
                st.rerun()
            with col_ap2:
              if st.button("Rejeitar Requisição Completa"):
                for _, row_item in df_itens_req.iterrows():
                  supabase.table("requisicoes").update(
                      {"Status": "Rejeitado"}
                  ).eq("id", row_item.get("id")).execute()
                registrar_log(
                    usuario_atual,
                    empresa_atual,
                    "Rejeicao Requisicao",
                    f"Cod: {codigo_escolhido}",
                )
                st.error(f"Requisição N° {codigo_escolhido} rejeitada.")
                st.rerun()
          else:
            st.success("Nenhuma requisição pendente de aprovação.")

          st.divider()
          st.subheader("Histórico Geral de Requisições")
          st.dataframe(
              df_reqs[
                  ["Codigo", "Produto", "Quantidade", "Nome Projeto", "Status"]
              ],
              use_container_width=True,
          )
        else:
          st.info("Nenhuma requisição registrada.")
      except Exception as e:
        st.error(f"Erro ao carregar workflow de aprovação: {e}")

    case "Gerencial":
      st.header("Módulo Gerencial & Financeiro")
      op_gerencial = st.radio(
          "Escolha uma Opção:",
          [
              "Fluxo de Caixa",
              "Contas a Pagar",
              "Contas a Receber",
              "DRE Gerencial",
              "Exportação de Dados",
          ],
          horizontal=True,
      )

      match op_gerencial:
        case "Fluxo de Caixa":
          fluxo_caixa = st.number_input("Valor a Cadastrar (R$)", step=10.0)
          if st.button("Salvar Valor"):
            try:
              supabase.table("fluxo_caixa").insert({
                  "Valor": float(fluxo_caixa),
                  "empresa_id": empresa_atual,
              }).execute()
              registrar_log(
                  usuario_atual,
                  empresa_atual,
                  "Cadastro Fluxo Caixa",
                  f"Valor: R$ {fluxo_caixa}",
              )
              st.success("Valor registrado com sucesso!")
            except Exception as e:
              st.error(f"Erro: {e}")

        case "Contas a Pagar":
          st.subheader("Cadastrar Conta a Pagar")
          try:
            res_f = (
                supabase.table("fornecedor")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_recebedor = pd.DataFrame(res_f.data if res_f.data else [])
            forn_lista = (
                sorted(
                    df_recebedor["Nome Fornecedor"].dropna().unique().tolist()
                )
                if not df_recebedor.empty
                and "Nome Fornecedor" in df_recebedor.columns
                else []
            )

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
                  "empresa_id": empresa_atual,
              }).execute()
              registrar_log(
                  usuario_atual,
                  empresa_atual,
                  "Nova Conta a Pagar",
                  f"NF: {nota_fiscal} | Valor: {valor}",
              )
              st.success("Fatura salva com sucesso!")

            res_cp = (
                supabase.table("contas_a_pagar")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_pagar = pd.DataFrame(res_cp.data if res_cp.data else [])
            if not df_pagar.empty and "Status" in df_pagar.columns:
              st.subheader("Faturas em Aberto")
              faturas_abertas = df_pagar[df_pagar["Status"] == "Aberto"]
              for i, row in faturas_abertas.iterrows():
                st.write(
                    f"NF: {row.get('NF', '')} | Fornecedor:"
                    f" {row.get('Fornecedor', '')} | Valor: R$"
                    f" {float(row.get('Valor', 0) or 0):,.2f} | Vencimento:"
                    f" {row.get('Vencimento', '')}"
                )
                if st.button(
                    f"Marcar como Paga - NF {row.get('NF', '')}",
                    key=f"pagar_{row.get('NF', '')}_{i}",
                ):
                  supabase.table("contas_a_pagar").update(
                      {"Status": "Pago"}
                  ).eq("NF", row["NF"]).eq("empresa_id", empresa_atual).execute()
                  registrar_log(
                      usuario_atual,
                      empresa_atual,
                      "Pagamento Efetuado",
                      f"NF: {row.get('NF', '')}",
                  )
                  st.success(f"Fatura {row.get('NF', '')} marcada como paga!")
                  st.rerun()
          except Exception as e:
            st.error(f"Erro em Contas a Pagar: {e}")

        case "Contas a Receber":
          st.subheader("Cadastrar Conta a Receber")
          try:
            res_f = (
                supabase.table("fornecedor")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_cliente = pd.DataFrame(res_f.data if res_f.data else [])
            cli_lista = (
                df_cliente["Nome Fornecedor"].tolist()
                if not df_cliente.empty
                and "Nome Fornecedor" in df_cliente.columns
                else []
            )

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
                  "empresa_id": empresa_atual,
              }).execute()
              registrar_log(
                  usuario_atual,
                  empresa_atual,
                  "Nova Conta a Receber",
                  f"Contrato: {contrato} | Valor: {valor}",
              )
              st.success("Fatura salva com sucesso!")

            res_cr = (
                supabase.table("contas_a_receber")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_receber = pd.DataFrame(res_cr.data if res_cr.data else [])
            if not df_receber.empty and "Status" in df_receber.columns:
              st.subheader("Faturas em Aberto")
              faturas_abertas = df_receber[df_receber["Status"] == "Aberto"]
              for i, row in faturas_abertas.iterrows():
                st.write(
                    f"Contrato: {row.get('Contrato', '')} | Cliente:"
                    f" {row.get('Cliente', '')} | Valor: R$"
                    f" {float(row.get('Valor', 0) or 0):,.2f} | Vencimento:"
                    f" {row.get('Vencimento', '')}"
                )
                if st.button(
                    "Marcar como Recebida - Contrato"
                    f" {row.get('Contrato', '')}",
                    key=f"receber_{row.get('Contrato', '')}_{i}",
                ):
                  supabase.table("contas_a_receber").update(
                      {"Status": "Recebido"}
                  ).eq("Contrato", row["Contrato"]).eq(
                      "empresa_id", empresa_atual
                  ).execute()
                  registrar_log(
                      usuario_atual,
                      empresa_atual,
                      "Recebimento Confirmado",
                      f"Contrato: {row.get('Contrato', '')}",
                  )
                  st.success(
                      f"Fatura do contrato {row.get('Contrato', '')} marcada"
                      " como recebida!"
                  )
                  st.rerun()
          except Exception as e:
            st.error(f"Erro em Contas a Receber: {e}")

        case "DRE Gerencial":
          st.subheader("Demonstrativo do Resultado do Exercício (DRE)")
          try:
            res_rec = (
                supabase.table("contas_a_receber")
                .select("Valor, Status")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            res_pag = (
                supabase.table("contas_a_pagar")
                .select("Valor, Status")
                .eq("empresa_id", empresa_atual)
                .execute()
            )

            df_rec = pd.DataFrame(res_rec.data if res_rec.data else [])
            df_pag = pd.DataFrame(res_pag.data if res_pag.data else [])

            total_receitas = (
                pd.to_numeric(
                    df_rec[df_rec["Status"] == "Recebido"]["Valor"],
                    errors="coerce",
                ).sum()
                if not df_rec.empty
                else 0.0
            )
            total_despesas = (
                pd.to_numeric(
                    df_pag[df_pag["Status"] == "Pago"]["Valor"], errors="coerce"
                ).sum()
                if not df_pag.empty
                else 0.0
            )
            lucro_liquido = total_receitas - total_despesas

            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric(
                "Receita Bruta (Recebida)", f"R$ {total_receitas:,.2f}"
            )
            col_d2.metric(
                "Despesas Operacionais (Pagas)", f"R$ {total_despesas:,.2f}"
            )
            col_d3.metric(
                "Resultado Líquido",
                f"R$ {lucro_liquido:,.2f}",
                delta=f"R$ {lucro_liquido:,.2f}",
            )

            tabela_dre = pd.DataFrame([
                {
                    "Rubrica": "(+) Receita Bruta Operacional",
                    "Valor (R$)": total_receitas,
                },
                {
                    "Rubrica": "(-) Despesas Operacionais / Custos",
                    "Valor (R$)": -total_despesas,
                },
                {
                    "Rubrica": "(=) Resultado Líquido do Exercício",
                    "Valor (R$)": lucro_liquido,
                },
            ])
            st.table(tabela_dre)
          except Exception as e:
            st.error(f"Erro ao consolidar DRE: {e}")

        case "Exportação de Dados":
          st.subheader("Exportação de Relatórios")
          try:
            res_exp_p = (
                supabase.table("produto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_exp_p = pd.DataFrame(res_exp_p.data if res_exp_p.data else [])

            if not df_exp_p.empty:
              csv_buffer = df_exp_p.to_csv(index=False).encode("utf-8")
              st.download_button(
                  label="Baixar Relatório de Estoque (CSV)",
                  data=csv_buffer,
                  file_name=f"estoque_{empresa_atual}.csv",
                  mime="text/csv",
              )
            else:
              st.info(
                  "Nenhum dado de estoque disponível para exportação."
              )
          except Exception as e:
            st.error(f"Erro na exportação: {e}")

    case "Auditoria":
      st.subheader("Registo de Auditoria (Audit Logs)")
      try:
        res_logs = (
            supabase.table("audit_logs")
            .select("*")
            .eq("empresa_id", empresa_atual)
            .order("id", desc=True)
            .limit(50)
            .execute()
        )
        df_logs = pd.DataFrame(res_logs.data if res_logs.data else [])
        if not df_logs.empty:
          st.dataframe(
              df_logs[["data_hora", "usuario", "acao", "detalhe"]],
              use_container_width=True,
          )
        else:
          st.info("Nenhum registo de auditoria encontrado.")
      except Exception as e:
        st.error(f"Erro ao carregar registos: {e}")

    case "Gestão Empresas":
      st.write("Cadastro de Clientes / Empresas (Tenants)")
      with st.form("form_cliente_empresa"):
        nome_empresa = st.text_input("Nome da Empresa / Cliente")
        cnpj_emp = st.text_input("CNPJ da Empresa")
        plano = st.selectbox(
            "Plano", ["Básico", "Profissional", "Enterprise"]
        )
        submit_emp = st.form_submit_button("Salvar Empresa")
        if submit_emp:
          try:
            supabase.table("clientes_empresas").insert({
                "Nome Empresa": nome_empresa,
                "CNPJ": cnpj_emp,
                "Plano": plano,
                "Status": "Ativo",
            }).execute()
            registrar_log(
                usuario_atual,
                empresa_atual,
                "Nova Empresa Cadastrada",
                nome_empresa,
            )
            st.success("Empresa cadastrada com sucesso!")
            st.rerun()
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

    case "Cadastros":
      cadastro_opcao = st.radio(
          "Escolha uma Opção:",
          [
              "Cadastro de Usuário",
              "Cadastro de Fornecedor",
              "Cadastro de Produto",
              "Cadastro Filial",
          ],
          horizontal=True,
      )
      match cadastro_opcao:
        case "Cadastro de Usuário":
          st.write("Gestão de Utilizadores e Permissões")
          sub_aba_usuario = st.radio(
              "Ação de Utilizador",
              ["Novo Utilizador", "Editar / Ativar-Inativar Utilizadores"],
              horizontal=True,
          )

          lista_emp_cadastradas = obter_lista_empresas()

          if not is_master and usuario_atual.lower() != "admin":
            lista_emp_cadastradas = [empresa_atual]

          if sub_aba_usuario == "Novo Utilizador":
            with st.form("form_usuario"):
              empresa_vinc = st.selectbox(
                  "Empresa do Utilizador", lista_emp_cadastradas
              )
              usuario = st.text_input("Usuário")
              email = st.text_input("E-mail")
              senha = st.text_input("Senha", type="password")
              status_inicial = st.selectbox("Status", ["Ativo", "Inativo"])

              st.write("Módulos Permitidos para Acesso:")
              p_graficos = st.checkbox("Gráficos Gerenciais", value=True)
              p_aprovacao = st.checkbox("Aprovacao Requisicao", value=True)
              p_cadastros = st.checkbox("Cadastros", value=True)
              p_almox = st.checkbox("Almoxarifado", value=True)
              p_compras = st.checkbox("Compras", value=True)
              p_gerencial = st.checkbox("Gerencial (Financeiro)", value=True)
              p_ia = st.checkbox("ATLAS IA", value=True)
              p_contratos = st.checkbox("Contratos", value=True)

              submitted = st.form_submit_button("Salvar Utilizador")
              if submitted:
                if usuario and email and senha:
                  modulos_escolhidos = []
                  if p_graficos:
                    modulos_escolhidos.append("Gráficos Gerenciais")
                  if p_aprovacao:
                    modulos_escolhidos.append("Aprovacao Requisicao")
                  if p_cadastros:
                    modulos_escolhidos.append("Cadastros")
                  if p_almox:
                    modulos_escolhidos.append("Almox")
                  if p_compras:
                    modulos_escolhidos.append("Compras")
                  if p_gerencial:
                    modulos_escolhidos.append("Gerencial")
                  if p_ia:
                    modulos_escolhidos.append("IA")
                  if p_contratos:
                    modulos_escolhidos.append("Contratos")

                  try:
                    supabase.table("usuarios").insert({
                        "Usuario": usuario.strip(),
                        "E-mail": email.strip(),
                        "Senha": senha.strip(),
                        "Empresa": empresa_vinc,
                        "ModulosPermitidos": ",".join(modulos_escolhidos),
                        "Status": status_inicial,
                    }).execute()
                    registrar_log(
                        usuario_atual,
                        empresa_atual,
                        "Utilizador Criado",
                        usuario.strip(),
                    )
                    st.success(f"Utilizador {usuario} criado com sucesso!")
                  except Exception as e:
                    st.error(f"Erro ao salvar utilizador: {e}")
                else:
                  st.warning("Preencha todos os campos obrigatórios.")
          else:
            st.subheader("Editar ou Alterar Estado de Utilizadores")
            try:
              res_todos_u = supabase.table("usuarios").select("*").execute()
              lista_u_dados = res_todos_u.data if res_todos_u.data else []

              if lista_u_dados:
                nomes_u = [u["Usuario"] for u in lista_u_dados]
                u_selecionado_nome = st.selectbox(
                    "Selecione o Utilizador para Editar", nomes_u
                )
                u_obj = next(
                    (
                        item
                        for item in lista_u_dados
                        if item["Usuario"] == u_selecionado_nome
                    ),
                    None,
                )

                if u_obj:
                  with st.form("form_edicao_usuario"):
                    novo_email = st.text_input(
                        "E-mail", value=u_obj.get("E-mail", "")
                    )
                    nova_senha = st.text_input(
                        "Senha", value=u_obj.get("Senha", ""), type="password"
                    )
                    idx_emp = (
                        lista_emp_cadastradas.index(u_obj.get("Empresa"))
                        if u_obj.get("Empresa") in lista_emp_cadastradas
                        else 0
                    )
                    nova_empresa = st.selectbox(
                        "Empresa", lista_emp_cadastradas, index=idx_emp
                    )

                    status_atual_db = u_obj.get("Status", "Ativo")
                    idx_status = 0 if status_atual_db == "Ativo" else 1
                    novo_status = st.selectbox(
                        "Status", ["Ativo", "Inativo"], index=idx_status
                    )

                    mods_atuais = str(u_obj.get("ModulosPermitidos", "")).split(
                        ","
                    )
                    st.write("Módulos Permitidos:")
                    ed_p_graficos = st.checkbox(
                        "Gráficos Gerenciais",
                        value=("Gráficos Gerenciais" in mods_atuais),
                    )
                    ed_p_aprovacao = st.checkbox(
                        "Aprovacao Requisicao",
                        value=("Aprovacao Requisicao" in mods_atuais),
                    )
                    ed_p_cadastros = st.checkbox(
                        "Cadastros", value=("Cadastros" in mods_atuais)
                    )
                    ed_p_almox = st.checkbox(
                        "Almoxarifado", value=("Almox" in mods_atuais)
                    )
                    ed_p_compras = st.checkbox(
                        "Compras", value=("Compras" in mods_atuais)
                    )
                    ed_p_gerencial = st.checkbox(
                        "Gerencial (Financeiro)",
                        value=("Gerencial" in mods_atuais),
                    )
                    ed_p_ia = st.checkbox(
                        "ATLAS IA", value=("IA" in mods_atuais)
                    )
                    ed_p_contratos = st.checkbox(
                        "Contratos", value=("Contratos" in mods_atuais)
                    )

                    btn_atualizar = st.form_submit_button(
                        "Atualizar Utilizador"
                    )
                    if btn_atualizar:
                      modulos_novos = []
                      if ed_p_graficos:
                        modulos_novos.append("Gráficos Gerenciais")
                      if ed_p_aprovacao:
                        modulos_novos.append("Aprovacao Requisicao")
                      if ed_p_cadastros:
                        modulos_novos.append("Cadastros")
                      if ed_p_almox:
                        modulos_novos.append("Almox")
                      if ed_p_compras:
                        modulos_novos.append("Compras")
                      if ed_p_gerencial:
                        modulos_novos.append("Gerencial")
                      if ed_p_ia:
                        modulos_novos.append("IA")
                      if ed_p_contratos:
                        modulos_novos.append("Contratos")

                      try:
                        supabase.table("usuarios").update({
                            "E-mail": novo_email.strip(),
                            "Senha": nova_senha.strip(),
                            "Empresa": nova_empresa,
                            "ModulosPermitidos": ",".join(modulos_novos),
                            "Status": novo_status,
                        }).eq("id", u_obj["id"]).execute()
                        registrar_log(
                            usuario_atual,
                            empresa_atual,
                            "Utilizador Editado",
                            u_selecionado_nome,
                        )
                        st.success(
                            f"Utilizador '{u_selecionado_nome}' atualizado com"
                            " sucesso!"
                        )
                      except Exception as err:
                        st.error(f"Erro ao atualizar: {err}")
            except Exception as ex:
              st.error(f"Erro ao carregar utilizadores: {ex}")

        case "Cadastro de Fornecedor":
          st.write("Cadastro de Fornecedor")
          with st.form("form_fornecedor"):
            nome_fornecedor = st.text_input("Razão Social")
            email_fornecedor = st.text_input("E-mail")
            cnpj_fornecedor = st.text_input("CNPJ")
            endereco_fornecedor = st.text_input("Endereço Completo")
            contato_fornecedor = st.text_input("Contato / Telefone")
            submitted = st.form_submit_button("Salvar Fornecedor")
            if submitted:
              try:
                supabase.table("fornecedor").insert({
                    "Nome Fornecedor": nome_fornecedor,
                    "E-mail Fornecedor": email_fornecedor,
                    "CNPJ": cnpj_fornecedor,
                    "Endereço": endereco_fornecedor,
                    "Contato Fornecedor": contato_fornecedor,
                    "empresa_id": empresa_atual,
                }).execute()
                registrar_log(
                    usuario_atual,
                    empresa_atual,
                    "Fornecedor Cadastrado",
                    nome_fornecedor,
                )
                st.success("Fornecedor Cadastrado com Sucesso!")
              except Exception as e:
                st.error(f"Erro ao salvar fornecedor: {e}")

        case "Cadastro de Produto":
          st.write("Cadastro de Produtos")
          descricao = st.text_input("Descrição Produto")
          ean_produto = st.text_input("Código de Barras")
          preco_produto = st.number_input(
              "Valor Produto", min_value=0.00, step=0.01, format="%.2f"
          )

          categorias = {
              "Consumo": [
                  "Alimentos",
                  "Bebidas",
                  "Produtos de limpeza",
                  "Higiene pessoal",
                  "Descartáveis",
              ],
              "Ferragem": [
                  "Parafusos e pregos",
                  "Ferramentas manuais",
                  "Fixadores",
                  "Fechaduras e cadeados",
                  "Abrasivos",
              ],
              "Escritório": [
                  "Material de escrita",
                  "Organização",
                  "Equipamentos de escritório",
                  "Mobiliário",
                  "Tecnologia",
              ],
              "Mecânica": [
                  "Ferramentas de precisão",
                  "Lubrificantes e óleos",
                  "Peças de reposição",
                  "Equipamentos de oficina",
                  "Instrumentos de medição",
              ],
              "Elétrica": [
                  "Cabos e fios",
                  "Conectores e tomadas",
                  "Iluminação",
                  "Disjuntores e quadros elétricos",
                  "Motores e transformadores",
              ],
              "Hidráulica": [
                  "Tubos e conexões",
                  "Válvulas e registros",
                  "Bombas hidráulicas",
                  "Torneiras e misturadores",
                  "Reservatórios e caixas d’água",
              ],
          }

          categoria_produto = st.selectbox(
              "Defina a Categoria", list(categorias.keys())
          )
          subcategoria_produto = st.selectbox(
              "Defina a Subcategoria", categorias[categoria_produto]
          )
          quantidade_produto = st.number_input("Quantidade", min_value=0)

          try:
            res_f = (
                supabase.table("filial")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_fil = pd.DataFrame(res_f.data if res_f.data else [])
            opcoes_filiais = ["Todas"] + (
                df_fil["Nome"].tolist()
                if not df_fil.empty and "Nome" in df_fil.columns
                else []
            )
          except Exception:
            opcoes_filiais = ["Todas"]

          filial_escolhida = st.selectbox("Filial", opcoes_filiais)

          if st.button("Salvar Cadastro"):
            try:
              res_prod = (
                  supabase.table("produto")
                  .select("Codigo")
                  .eq("empresa_id", empresa_atual)
                  .order("Codigo", desc=True)
                  .limit(1)
                  .execute()
              )
              dados_ult = res_prod.data
              novo_codigo = (
                  (int(dados_ult[0]["Codigo"]) + 1)
                  if dados_ult and dados_ult[0].get("Codigo") is not None
                  else 1
              )
            except Exception:
              novo_codigo = 1

            lista_produtos = [{
                "Codigo": novo_codigo,
                "Descrição Produto": descricao,
                "ean_produto": ean_produto,
                "Preço Produto": float(preco_produto),
                "Categoria": categoria_produto,
                "Sub-Categoria": subcategoria_produto,
                "Quantidade Produto": int(quantidade_produto),
                "Filial": str(filial_escolhida),
                "empresa_id": empresa_atual,
            }]

            try:
              supabase.table("produto").insert(lista_produtos).execute()
              registrar_log(
                  usuario_atual,
                  empresa_atual,
                  "Produto Cadastrado",
                  descricao,
              )
              st.success(
                  f"Produto código {novo_codigo} cadastrado com sucesso!"
              )
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
                    "empresa_id": empresa_atual,
                }).execute()
                registrar_log(
                    usuario_atual, empresa_atual, "Filial Cadastrada", nome
                )
                st.success("Filial Cadastrada com Sucesso!")
              except Exception as e:
                st.error(f"Erro ao salvar filial: {e}")

    case "Almox":
      st.header("Almoxarifado & Gestão de Materiais")
      menu_almox = st.radio(
          "Escolha uma Opção",
          [
              "Consulta Estoque",
              "Requisição de Compras",
              "Consumo Direto / Aplicação",
              "Ajuste de Estoque",
              "Recebimento",
              "Situação de Pedidos",
          ],
          horizontal=True,
      )

      match menu_almox:
        case "Consulta Estoque":
          try:
            res = (
                supabase.table("produto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            painel_estoque = pd.DataFrame(res.data if res.data else [])
            if not painel_estoque.empty:
              st.dataframe(painel_estoque, use_container_width=True)
            else:
              st.info("Nenhum produto cadastrado.")
          except Exception as e:
            st.error(f"Erro ao carregar estoque: {e}")

        case "Requisição de Compras":
          try:
            res_p = (
                supabase.table("produto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            res_f = (
                supabase.table("filial")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            res_proj = (
                supabase.table("projeto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )

            df_produtos = pd.DataFrame(res_p.data if res_p.data else [])
            df_filial = pd.DataFrame(res_f.data if res_f.data else [])
            df_nome_projeto = pd.DataFrame(res_proj.data if res_proj.data else [])

            prod_lista = (
                df_produtos["Descrição Produto"].unique().tolist()
                if not df_produtos.empty
                and "Descrição Produto" in df_produtos.columns
                else []
            )
            fil_lista = (
                df_filial["Nome"].unique().tolist()
                if not df_filial.empty and "Nome" in df_filial.columns
                else []
            )
            proj_desc = (
                df_nome_projeto["Descrição"].unique().tolist()
                if not df_nome_projeto.empty
                and "Descrição" in df_nome_projeto.columns
                else []
            )
            proj_num = (
                df_nome_projeto["Número Projeto"].unique().tolist()
                if not df_nome_projeto.empty
                and "Número Projeto" in df_nome_projeto.columns
                else []
            )

            produto_escolhido = st.selectbox("Produto", prod_lista)
            quantidade = st.number_input("Quantidade", min_value=1)
            filial = st.selectbox("Filial Solicitante", fil_lista)
            nome_projeto = st.selectbox(
                "Descrição do Projeto / Obra", proj_desc
            )
            n_projeto = st.selectbox("Número Projeto / OS", proj_num)

            if "item_requisicao" not in st.session_state:
              st.session_state.item_requisicao = []

            if st.button("Adicionar Produto"):
              item = {
                  "Produto": produto_escolhido,
                  "Quantidade": int(quantidade),
                  "Filial Requisitante": filial,
                  "Nome Projeto": nome_projeto,
                  "N° Projeto": str(n_projeto),
                  "empresa_id": empresa_atual,
              }
              st.session_state.item_requisicao.append(item)
              st.success(
                  f"Produto {produto_escolhido} adicionado (Qtd: {quantidade})"
              )

            if len(st.session_state.item_requisicao) > 0:
              st.subheader("Itens adicionados à requisição")
              st.table(pd.DataFrame(st.session_state.item_requisicao))

            if st.button("Salvar Requisição"):
              try:
                res_req = (
                    supabase.table("requisicoes")
                    .select("Codigo")
                    .eq("empresa_id", empresa_atual)
                    .order("Codigo", desc=True)
                    .limit(1)
                    .execute()
                )
                ult_req = res_req.data
                novo_codigo = (
                    (int(ult_req[0]["Codigo"]) + 1)
                    if ult_req and ult_req[0].get("Codigo") is not None
                    else 1
                )
              except Exception:
                novo_codigo = 1

              nova_requisicao = [{
                  "Codigo": novo_codigo,
                  "Status": "Aguardando Aprovação",
                  **item,
              } for item in st.session_state.item_requisicao]

              supabase.table("requisicoes").insert(nova_requisicao).execute()
              registrar_log(
                  usuario_atual,
                  empresa_atual,
                  "Nova Requisição Criada",
                  f"Código: {novo_codigo} (Aguardando Aprovação)",
              )
              st.success(
                  f"Requisição N° {novo_codigo} gravada e enviada para"
                  " Aprovação do Gestor!"
              )
              st.session_state.item_requisicao = []
          except Exception as e:
            st.error(f"Erro na requisição: {e}")

        case "Consumo Direto / Aplicação":
          st.subheader("Baixa de Material por Aplicação")
          st.caption(
              "Registre a saída de materiais do estoque para aplicação direta"
              " em uma obra ou embarcação."
          )
          try:
            res_p = (
                supabase.table("produto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            res_proj = (
                supabase.table("projeto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_p = pd.DataFrame(res_p.data if res_p.data else [])
            df_proj = pd.DataFrame(res_proj.data if res_proj.data else [])

            if not df_p.empty and not df_proj.empty:
              prod_sel = st.selectbox(
                  "Selecione o Material",
                  df_p["Descrição Produto"].unique().tolist(),
              )
              proj_sel = st.selectbox(
                  "Selecione o Projeto / Obra Destino",
                  df_proj["Descrição"].unique().tolist(),
              )

              row_prod = df_p[df_p["Descrição Produto"] == prod_sel].iloc[0]
              qtd_disp = int(row_prod.get("Quantidade Produto", 0) or 0)

              st.info(
                  f"Quantidade disponível em estoque: **{qtd_disp} un.**"
              )
              qtd_consumo = st.number_input(
                  "Quantidade Aplicada/Consumida",
                  min_value=1,
                  max_value=max(1, qtd_disp),
                  step=1,
              )
              obs_consumo = st.text_input(
                  "Observação / Canteiro / Local Exato"
              )

              if st.button("Confirmar Consumo Direto"):
                nova_qtd = qtd_disp - int(qtd_consumo)
                supabase.table("produto").update(
                    {"Quantidade Produto": nova_qtd}
                ).eq("id", row_prod["id"]).execute()

                supabase.table("ajuste_estoque").insert({
                    "Produto": str(prod_sel),
                    "Quantidade": int(qtd_consumo),
                    "Motivo Ajuste": (
                        f"Consumo Direto / Obra: {proj_sel} ({obs_consumo})"
                    ),
                    "Filial": str(row_prod.get("Filial", "Todas")),
                    "empresa_id": empresa_atual,
                }).execute()

                registrar_log(
                    usuario_atual,
                    empresa_atual,
                    "Consumo Direto Obra",
                    f"Material: {prod_sel} | Qtd: {qtd_consumo} | Obra:"
                    f" {proj_sel}",
                )
                st.success(
                    "Consumo registrado com sucesso! Estoque atualizado."
                )
                st.rerun()
            else:
              st.warning(
                  "É necessário ter produtos e projetos cadastrados para"
                  " registrar o consumo."
              )
          except Exception as e:
            st.error(f"Erro ao registrar consumo: {e}")

        case "Ajuste de Estoque":
          try:
            res_p = (
                supabase.table("produto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_produtos = pd.DataFrame(res_p.data if res_p.data else [])

            if not df_produtos.empty:
              df_produtos["Label_Prod"] = (
                  df_produtos["Descrição Produto"].astype(str)
                  + " (Filial: "
                  + df_produtos.get("Filial", "Todas").astype(str)
                  + " - Atual: "
                  + df_produtos.get("Quantidade Produto", 0).astype(str)
                  + ")"
              )

              produto_selecionado_label = st.selectbox(
                  "Selecione o Produto", df_produtos["Label_Prod"].tolist()
              )
              produto_obj = df_produtos[
                  df_produtos["Label_Prod"] == produto_selecionado_label
              ].iloc[0]

              ajuste_quantidade = st.number_input(
                  "Nova Quantidade",
                  min_value=0,
                  value=int(produto_obj.get("Quantidade Produto", 0) or 0),
              )
              ajuste_motivos = st.selectbox(
                  "Motivo Ajuste",
                  [
                      "Avaria",
                      "Inventário",
                      "Perda/Dano em Obra",
                      "Ajuste Técnico",
                  ],
              )

              if st.button("Salvar Ajuste"):
                produto_id = produto_obj["id"]
                nome_prod = produto_obj["Descrição Produto"]

                supabase.table("ajuste_estoque").insert({
                    "Produto": str(nome_prod),
                    "Quantidade": int(ajuste_quantidade),
                    "Motivo Ajuste": ajuste_motivos,
                    "Filial": str(produto_obj.get("Filial", "Todas")),
                    "empresa_id": empresa_atual,
                }).execute()

                supabase.table("produto").update(
                    {"Quantidade Produto": int(ajuste_quantidade)}
                ).eq("id", produto_id).execute()

                registrar_log(
                    usuario_atual,
                    empresa_atual,
                    "Ajuste Estoque",
                    f"Produto: {nome_prod} | Nova Qtd: {ajuste_quantidade}",
                )
                st.success(
                    "Ajuste Realizado com Sucesso! O estoque foi atualizado."
                )
                st.rerun()
            else:
              st.info(
                  "Nenhum produto cadastrado para realizar ajuste."
              )
          except Exception as e:
            st.error(f"Erro no ajuste de estoque: {e}")

        case "Recebimento":
          st.subheader("Recebimento de Mercadorias & Leitura Mobile")

          modo_recebimento = st.radio(
              "Modo de Operação",
              [
                  "Recebimento Mobile / Rápido",
                  "Conferência por Pedido (Manual)",
              ],
              horizontal=True,
          )

          if modo_recebimento == "Recebimento Mobile / Rápido":
            st.info(
                "Utilize a câmara do dispositivo para capturar boletos, notas"
                " fiscais ou ler o código do produto."
            )

            with st.expander(
                "Dados do Documento Fiscal & Pagamento", expanded=True
            ):
              col_doc1, col_doc2 = st.columns(2)
              with col_doc1:
                numero_nota_fiscal = st.text_input(
                    "Número da Nota Fiscal (NF)", placeholder="Ex: 001234"
                )
              with col_doc2:
                cod_barras_boleto = st.text_input(
                    "Linha Digitável / Código de Barras do Boleto",
                    placeholder="Cole ou digite a linha digitável",
                )

            st.divider()

            col_mob1, col_mob2 = st.columns([1, 1])
            with col_mob1:
              foto_capturada = st.camera_input(
                  "Focar no Código de Barras / Embalagem / Documento"
              )

            with col_mob2:
              ean_buscado = st.text_input(
                  "Digitar ou Bipar Código de Barras / EAN"
              )

              if ean_buscado:
                try:
                  res_ean = (
                      supabase.table("produto")
                      .select("*")
                      .eq("ean_produto", ean_buscado.strip())
                      .eq("empresa_id", empresa_atual)
                      .execute()
                  )
                  prod_encontrados = res_ean.data if res_ean.data else []
                  if prod_encontrados:
                    p_item = prod_encontrados[0]
                    st.success(
                        "Item Identificado:"
                        f" **{p_item.get('Descrição Produto')}**"
                    )
                    st.caption(
                        f"Filial: {p_item.get('Filial')} | Qtd Atual:"
                        f" {p_item.get('Quantidade Produto')}"
                    )

                    qtd_add = st.number_input(
                        "Quantidade a Entrar", min_value=1, value=1, step=1
                    )
                    if st.button("Confirmar Entrada Rápida"):
                      nova_qtd = int(
                          p_item.get("Quantidade Produto", 0) or 0
                      ) + int(qtd_add)
                      supabase.table("produto").update(
                          {"Quantidade Produto": nova_qtd}
                      ).eq("id", p_item["id"]).execute()

                      detalhe_log = (
                          f"Produto: {p_item.get('Descrição Produto')} | Qtd"
                          f" Entrada: {qtd_add}"
                      )
                      if numero_nota_fiscal:
                        detalhe_log += f" | NF: {numero_nota_fiscal}"
                      if cod_barras_boleto:
                        detalhe_log += f" | Boleto: {cod_barras_boleto}"

                      registrar_log(
                          usuario_atual,
                          empresa_atual,
                          "Recebimento Mobile",
                          detalhe_log,
                      )
                      st.success(
                          "Estoque e registo de recebimento atualizados com"
                          " sucesso!"
                      )
                      st.rerun()
                  else:
                    st.warning(
                        "Nenhum produto cadastrado com este código EAN."
                    )
                except Exception as e_ean:
                  st.error(f"Erro na busca por EAN: {e_ean}")

          else:
            try:
              res_v = (
                  supabase.table("vencedores")
                  .select("*")
                  .eq("empresa_id", empresa_atual)
                  .execute()
              )
              df_pedido = pd.DataFrame(res_v.data if res_v.data else [])
              if (
                  not df_pedido.empty
                  and "NumeroPedido" in df_pedido.columns
                  and "Fornecedor" in df_pedido.columns
              ):
                df_pedido["PedidoLabel"] = (
                    df_pedido["NumeroPedido"].astype(str)
                    + " - "
                    + df_pedido["Fornecedor"].astype(str)
                )
                pedido = st.selectbox(
                    "Selecione o Pedido para Recebimento",
                    df_pedido["PedidoLabel"].unique().tolist(),
                )

                numero_pedido, fornecedor = str(pedido).split(" - ", 1)
                df_itens_pedido = df_pedido[
                    (df_pedido["NumeroPedido"].astype(str) == numero_pedido)
                    & (df_pedido["Fornecedor"].astype(str) == fornecedor)
                ]

                st.write("Itens do Pedido:")
                st.table(df_itens_pedido[["Produto", "Preço Cotado"]])

                res_p = (
                    supabase.table("produto")
                    .select("*")
                    .eq("empresa_id", empresa_atual)
                    .execute()
                )
                df_produto = pd.DataFrame(res_p.data if res_p.data else [])
                filiais = (
                    df_produto["Filial"].unique().tolist()
                    if not df_produto.empty and "Filial" in df_produto.columns
                    else []
                )
                filial_escolhida = st.selectbox(
                    "Selecione a Filial de Entrada", filiais
                )

                novo_status_recebimento = st.selectbox(
                    "Status de Entrega",
                    [
                        "Entregue Total",
                        "Entregue Parcial",
                        "Em Trânsito",
                        "Aguardando Faturamento",
                    ],
                )

                recebimentos = {}
                for _, row in df_itens_pedido.iterrows():
                  qtd_recebida = st.number_input(
                      f"Quantidade recebida de {row['Produto']}",
                      min_value=0,
                      step=1,
                  )
                  recebimentos[row["Produto"]] = int(qtd_recebida)

                if st.button("Confirmar Recebimento"):
                  for produto, qtd in recebimentos.items():
                    if qtd > 0:
                      res_q = (
                          supabase.table("produto")
                          .select("*")
                          .eq("Descrição Produto", produto)
                          .eq("empresa_id", empresa_atual)
                          .execute()
                      )
                      prod_matches = res_q.data if res_q.data else []

                      if prod_matches:
                        row_p = next(
                            (
                                p
                                for p in prod_matches
                                if p.get("Filial") == filial_escolhida
                            ),
                            prod_matches[0],
                        )
                        qtd_atual = int(
                            row_p.get("Quantidade Produto", 0) or 0
                        )
                        novo_total = qtd_atual + int(qtd)
                        supabase.table("produto").update(
                            {"Quantidade Produto": novo_total}
                        ).eq("id", row_p["id"]).execute()

                  try:
                    ids_para_atualizar = (
                        df_itens_pedido["id"].tolist()
                        if "id" in df_itens_pedido.columns
                        else []
                    )
                    if ids_para_atualizar:
                      for id_item in ids_para_atualizar:
                        supabase.table("vencedores").update(
                            {"Situacao": novo_status_recebimento}
                        ).eq("id", id_item).execute()
                  except Exception:
                    pass

                  registrar_log(
                      usuario_atual,
                      empresa_atual,
                      "Recebimento Mercadoria",
                      f"Pedido: {numero_pedido} - Status:"
                      f" {novo_status_recebimento}",
                  )
                  st.success(
                      "Estoque atualizado e status alterado para"
                      f" '{novo_status_recebimento}'!"
                  )
                  st.rerun()
            except Exception as e:
              st.error(f"Erro no recebimento: {e}")

        case "Situação de Pedidos":
          st.subheader("Gestão da Situação de Pedidos de Compra")
          try:
            res_ped = (
                supabase.table("vencedores")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_ped = pd.DataFrame(res_ped.data if res_ped.data else [])
            if not df_ped.empty:
              if "Situacao" not in df_ped.columns:
                df_ped["Situacao"] = "Pendente"
              df_ped["Situacao"] = df_ped["Situacao"].fillna("Pendente")
              st.dataframe(
                  df_ped[[
                      "NumeroPedido",
                      "Fornecedor",
                      "Produto",
                      "Preço Cotado",
                      "Situacao",
                  ]],
                  use_container_width=True,
              )
            else:
              st.info("Nenhum pedido de compra registado.")
          except Exception as e:
            st.error(f"Erro ao carregar pedidos: {e}")

    case "Compras":
      st.header("Módulo de Compras & Gestão de Suprimentos")
      escolha_compras = st.radio(
          "Escolha uma Opção:",
          [
              "Gestão de Compras",
              "Definição de Vencedores",
              "Pedidos de Compras",
          ],
          horizontal=True,
      )
      match escolha_compras:
        case "Gestão de Compras":
          try:
            res_r = (
                supabase.table("requisicoes")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            res_f = (
                supabase.table("fornecedor")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )

            df_req_gestao = pd.DataFrame(res_r.data if res_r.data else [])
            df_req_fornecedor = pd.DataFrame(res_f.data if res_f.data else [])

            if (
                not df_req_gestao.empty
                and "Status" in df_req_gestao.columns
            ):
              df_req_gestao = df_req_gestao[
                  df_req_gestao["Status"] == "Aprovado"
              ]

            if (
                not df_req_gestao.empty
                and not df_req_fornecedor.empty
                and "Codigo" in df_req_gestao.columns
            ):
              df_req_gestao["Codigo"] = (
                  df_req_gestao["Codigo"].fillna(0).astype(str)
              )
              df_req_gestao["Nome Projeto"] = (
                  df_req_gestao.get("Nome Projeto", "").fillna("").astype(str)
              )
              df_req_gestao["Requisicao_Label"] = (
                  df_req_gestao["Codigo"] + " - " + df_req_gestao["Nome Projeto"]
              )

              requisicao_compra = st.selectbox(
                  "Requisição Aprovada",
                  df_req_gestao["Requisicao_Label"].unique().tolist(),
              )
              req_fornecedor = st.selectbox(
                  "Escolha o Fornecedor", df_req_fornecedor["Nome Fornecedor"]
              )
              tipo_frete = st.selectbox("Modalidade de Frete", ["CIF", "FOB"])
              codigo_selecionado = str(requisicao_compra).split(" - ")[0]
              data_emissao = st.date_input("Data de Emissão do Pedido")
              data_recebimento = st.date_input("Data de Recebimento do Pedido")

              df_filtrada = df_req_gestao[
                  df_req_gestao["Codigo"] == codigo_selecionado
              ].copy()
              df_filtrada["Preço Cotado"] = 0.00
              df_filtrada["Ultimo Fornecedor"] = "N/D"
              df_filtrada["Ultimo Preço R$"] = 0.00

              try:
                res_cot_hist = (
                    supabase.table("vencedores")
                    .select("Produto, Fornecedor, Preço Cotado")
                    .eq("empresa_id", empresa_atual)
                    .execute()
                )
                df_hist = pd.DataFrame(
                    res_cot_hist.data if res_cot_hist.data else []
                )
                if not df_hist.empty and "Produto" in df_hist.columns:
                  for idx, row in df_filtrada.iterrows():
                    prod_nome = row["Produto"]
                    match_prod = df_hist[df_hist["Produto"] == prod_nome]
                    if not match_prod.empty:
                      ult_reg = match_prod.iloc[-1]
                      df_filtrada.at[idx, "Ultimo Fornecedor"] = str(
                          ult_reg.get("Fornecedor", "N/D")
                      )
                      df_filtrada.at[idx, "Ultimo Preço R$"] = float(
                          ult_reg.get("Preço Cotado", 0.0) or 0.0
                      )
              except Exception:
                pass

              st.subheader("Itens da Requisição & Histórico de Última Compra")
              df_editado = st.data_editor(
                  df_filtrada,
                  use_container_width=True,
                  column_config={
                      "Preço Cotado": st.column_config.NumberColumn(
                          "Preço Cotado (R$)", format="R$ %.2f", min_value=0.0
                      )
                  },
              )

              if st.button("Salvar Cotação"):
                for col_remover in [
                    "Requisicao_Label",
                    "id",
                    "empresa_id",
                    "Ultimo Fornecedor",
                    "Ultimo Preço R$",
                    "Status",
                ]:
                  if col_remover in df_editado.columns:
                    df_editado = df_editado.drop(columns=[col_remover])

                df_editado["Codigo"] = codigo_selecionado
                df_editado["Requisição"] = str(requisicao_compra)
                df_editado["Fornecedor"] = str(req_fornecedor)
                df_editado["Frete"] = tipo_frete
                df_editado["Data Emissão"] = str(data_emissao)
                df_editado["Data Recebimento"] = str(data_recebimento)
                df_editado["empresa_id"] = empresa_atual

                df_editado["Preço Cotado"] = pd.to_numeric(
                    df_editado["Preço Cotado"], errors="coerce"
                ).fillna(0.0)

                dados_inserir = df_editado.to_dict(orient="records")
                supabase.table("cotacoes").insert(dados_inserir).execute()
                registrar_log(
                    usuario_atual,
                    empresa_atual,
                    "Cotação Registada",
                    f"Fornecedor: {req_fornecedor}",
                )
                st.success("Cotação salva com sucesso!")
                st.rerun()
            else:
              st.info(
                  "Sem requisições aprovadas disponíveis para cotação."
              )
          except Exception as e:
            st.error(f"Erro na gestão de compras: {e}")

        case "Definição de Vencedores":
          try:
            res_c = (
                supabase.table("cotacoes")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df = pd.DataFrame(res_c.data if res_c.data else [])
            if not df.empty and "Codigo" in df.columns:
              codigos_unicos = df["Codigo"].unique().tolist()
              codigo_escolhido = st.selectbox(
                  "Escolha o Código da Requisição", codigos_unicos
              )

              df_filtrado = df[
                  df["Codigo"].astype(str) == str(codigo_escolhido)
              ].copy()

              col_preco = (
                  "Preço Cotado" if "Preço Cotado" in df_filtrado.columns else "preco"
              )
              df_filtrado[col_preco] = pd.to_numeric(
                  df_filtrado[col_preco], errors="coerce"
              ).fillna(0.0)

              tabela = df_filtrado.pivot_table(
                  index="Produto",
                  columns="Fornecedor",
                  values=col_preco,
                  aggfunc="last",
              ).fillna(0.0)

              def highlight_min(s):
                s_valid = s[s > 0]
                if not s_valid.empty:
                  min_val = s_valid.min()
                  return [
                      "background-color: #2e7d32; color: white;"
                      " font-weight: bold;"
                      if v == min_val
                      else ""
                      for v in s
                  ]
                return ["" for _ in s]

              st.write(
                  "Comparativo de Cotações (Menor preço em destaque)"
              )
              st.dataframe(
                  tabela.style.apply(highlight_min, axis=1).format("R$ {:.2f}"),
                  use_container_width=True,
              )

              vencedores = {}
              for produto, linha in tabela.iterrows():
                linha_valid = linha[linha > 0]
                fornecedor_min = (
                    linha_valid.idxmin() if not linha_valid.empty else None
                )
                st.write(f"**Produto:** {produto}")
                for fornecedor, valor in linha.items():
                  default = fornecedor == fornecedor_min
                  vencedores[(produto, fornecedor)] = st.checkbox(
                      f"{fornecedor} - R$ {float(valor or 0):.2f}",
                      value=default,
                      key=f"{produto}_{fornecedor}",
                  )

              if st.button("Definir Vencedores"):
                try:
                  res_v = (
                      supabase.table("vencedores")
                      .select("NumeroPedido")
                      .eq("empresa_id", empresa_atual)
                      .order("NumeroPedido", desc=True)
                      .limit(1)
                      .execute()
                  )
                  ult_v = res_v.data
                  proximo_numero = (
                      (int(ult_v[0]["NumeroPedido"]) + 1)
                      if ult_v and ult_v[0].get("NumeroPedido") is not None
                      else 1
                  )
                except Exception:
                  proximo_numero = 1

                selecionados = [{
                    "Produto": str(prod),
                    "Fornecedor": str(forn),
                    "Preço Cotado": float(tabela.loc[prod, forn]),
                    "Quantidade": (
                        int(
                            df_filtrado[
                                (df_filtrado["Produto"] == prod)
                                & (df_filtrado["Fornecedor"] == forn)
                            ]["Quantidade"].values[0]
                        )
                        if "Quantidade" in df_filtrado.columns
                        else 1
                    ),
                    "Frete": (
                        str(
                            df_filtrado[
                                (df_filtrado["Produto"] == prod)
                                & (df_filtrado["Fornecedor"] == forn)
                            ]["Frete"].values[0]
                        )
                        if "Frete" in df_filtrado.columns
                        else "CIF"
                    ),
                    "Selecionado": True,
                    "NumeroPedido": int(proximo_numero),
                    "Situacao": "Pendente",
                    "empresa_id": empresa_atual,
                } for (prod, forn), marcado in vencedores.items() if marcado]

                if selecionados:
                  supabase.table("vencedores").insert(selecionados).execute()
                  st.success(
                      "Vencedores definidos com sucesso! Número do pedido:"
                      f" {proximo_numero}"
                  )
                  registrar_log(
                      usuario_atual,
                      empresa_atual,
                      "Vencedores Definidos",
                      f"Pedido: {proximo_numero}",
                  )
          except Exception as e:
            st.error(f"Erro ao definir vencedores: {e}")

        case "Pedidos de Compras":
          try:
            res_v = (
                supabase.table("vencedores")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_pedido = pd.DataFrame(res_v.data if res_v.data else [])

            if not df_pedido.empty and "NumeroPedido" in df_pedido.columns:
              df_pedido["PedidoLabel"] = (
                  df_pedido["NumeroPedido"].astype(str)
                  + " - "
                  + df_pedido["Fornecedor"].astype(str)
              )
              pedido = st.selectbox(
                  "Selecione um Pedido de Compra",
                  df_pedido["PedidoLabel"].unique().tolist(),
              )

              numero_pedido, fornecedor_nome = str(pedido).split(" - ", 1)

              res_emp_data = (
                  supabase.table("clientes_empresas")
                  .select("*")
                  .ilike("Nome Empresa", empresa_atual.strip())
                  .execute()
              )
              emp_info = (
                  res_emp_data.data[0]
                  if res_emp_data.data
                  else {
                      "CNPJ": "00.000.000/0001-00",
                      "Nome Empresa": empresa_atual,
                  }
              )

              res_forn_data = (
                  supabase.table("fornecedor")
                  .select("*")
                  .ilike("Nome Fornecedor", fornecedor_nome.strip())
                  .eq("empresa_id", empresa_atual)
                  .execute()
              )
              forn_info = (
                  res_forn_data.data[0]
                  if res_forn_data.data
                  else {
                      "CNPJ": "00.000.000/0001-00",
                      "Endereço": "N/D",
                      "Contato Fornecedor": "N/D",
                  }
              )

              buffer = io.BytesIO()
              doc = SimpleDocTemplate(
                  buffer,
                  pagesize=A4,
                  rightMargin=30,
                  leftMargin=30,
                  topMargin=30,
                  bottomMargin=30,
              )
              elementos = []

              estilos = getSampleStyleSheet()
              estilo_normal = estilos["Normal"]
              estilo_normal.fontSize = 9
              estilo_normal.leading = 11

              if os.path.exists("capsuleSys.png"):
                img_rl = RLImage("capsuleSys.png", width=120, height=45)
                txt_topo = Paragraph(
                    f"<b>{emp_info.get('Nome Empresa', empresa_atual)}</b><br/>CNPJ:"
                    f" {emp_info.get('CNPJ', 'N/D')}<br/><font size=12"
                    " color='#003366'><b>PEDIDO DE COMPRA N°"
                    f" {numero_pedido}</b></font><br/>DATA:"
                    f" {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    estilo_normal,
                )
                tbl_cab = Table([[txt_topo, img_rl]], colWidths=[380, 150])
                tbl_cab.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ]))
                elementos.append(tbl_cab)
              else:
                txt_topo = (
                    f"<b>{emp_info.get('Nome Empresa', empresa_atual)}</b><br/>CNPJ:"
                    f" {emp_info.get('CNPJ', 'N/D')}<br/><font size=12"
                    " color='#003366'><b>PEDIDO DE COMPRA N°"
                    f" {numero_pedido}</b></font><br/>DATA:"
                    f" {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                )
                elementos.append(Paragraph(txt_topo, estilo_normal))

              elementos.append(Spacer(1, 15))

              texto_fornecedor = f"""
                            <b>Fornecedor:</b> {forn_info.get('Nome Fornecedor', fornecedor_nome)}<br/>
                            <b>CNPJ:</b> {forn_info.get('CNPJ', 'N/D')}<br/>
                            <b>Endereço:</b> {forn_info.get('Endereço', 'N/D')}<br/>
                            <b>Contato:</b> {forn_info.get('Contato Fornecedor', 'N/D')}
                            """
              elementos.append(Paragraph(texto_fornecedor, estilo_normal))
              elementos.append(Spacer(1, 15))

              df_itens_pedido = df_pedido[
                  (df_pedido["NumeroPedido"].astype(str) == numero_pedido)
                  & (df_pedido["Fornecedor"] == fornecedor_nome)
              ]

              dados_tabela = [["Produto", "Quant", "Valor Unit", "Subtotal"]]
              subtotal_geral = 0.0

              for _, row in df_itens_pedido.iterrows():
                val_qtd = row.get("Quantidade", 1)
                if pd.isna(val_qtd) or str(val_qtd).lower() == "nan":
                  qtd = 1.0
                else:
                  try:
                    qtd = float(val_qtd)
                  except ValueError:
                    qtd = 1.0

                val_unit = row.get("Preço Cotado", 0.0)
                if pd.isna(val_unit) or str(val_unit).lower() == "nan":
                  vl_unit = 0.0
                else:
                  try:
                    vl_unit = float(val_unit)
                  except ValueError:
                    vl_unit = 0.0

                subtotal = qtd * vl_unit
                subtotal_geral += subtotal

                dados_tabela.append([
                    str(row.get("Produto", "")),
                    f"{qtd:,.0f}" if qtd.is_integer() else f"{qtd:,.2f}",
                    f"R$ {vl_unit:,.2f}",
                    f"R$ {subtotal:,.2f}",
                ])

              tabela_pdf = Table(
                  dados_tabela, colWidths=[230, 70, 100, 100]
              )
              tabela_pdf.setStyle(TableStyle([
                  ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                  ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                  ("FONTSIZE", (0, 0), (-1, -1), 8),
                  ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
              ]))
              elementos.append(tabela_pdf)
              elementos.append(Spacer(1, 15))

              frete_modalidade = (
                  df_itens_pedido.iloc[0].get("Frete", "CIF")
                  if not df_itens_pedido.empty
                  else "CIF"
              )
              texto_totais = f"""
                            <b>Modalidade de Frete:</b> {frete_modalidade}<br/>
                            <b>Subtotal Geral:</b> R$ {subtotal_geral:,.2f}<br/>
                            <b>Total Geral do Pedido:</b> R$ {subtotal_geral:,.2f}
                            """
              elementos.append(Paragraph(texto_totais, estilo_normal))

              doc.build(elementos)
              buffer.seek(0)

              st.download_button(
                  label="Baixar Pedido de Compra (PDF)",
                  data=buffer,
                  file_name=(
                      f"pedido_compra_{numero_pedido}_{fornecedor_nome}.pdf"
                  ),
                  mime="application/pdf",
              )
          except Exception as e:
            st.error(f"Erro ao gerar pedido: {e}")

    case "IA":
      st.subheader(
          "ATLAS IA — Central de Comando por Voz & Inteligência Estratégica"
      )
      st.caption(
          "Converse por voz com o ATLAS IA. Ele analisa os dados do seu ERP em"
          " tempo real para responder sobre estoques, cotações e finanças."
      )

      def obter_contexto_completo_erp(empresa_alvo):
        dados_contexto = f"Empresa Ativa: {empresa_alvo}\n"

        tabelas_mapeadas = [
            ("PRODUTOS / ESTOQUE", "produto"),
            ("PROJETOS / OBRAS", "projeto"),
            ("REQUISIÇÕES DE COMPRA", "requisicoes"),
            ("COTAÇÕES DE COMPRA", "cotacoes"),
            ("VENCEDORES / PEDIDOS DE COMPRA", "vencedores"),
            ("FORNECEDORES CADASTRADOS", "fornecedor"),
            ("CONTAS A PAGAR", "contas_a_pagar"),
            ("CONTAS A RECEBER", "contas_a_receber"),
            ("FLUXO DE CAIXA", "fluxo_caixa"),
            ("CONTRATOS REGISTRADOS", "contrato"),
        ]

        for titulo, nome_tabela in tabelas_mapeadas:
          try:
            res = (
                supabase.table(nome_tabela)
                .select("*")
                .eq("empresa_id", empresa_alvo)
                .execute()
            )
            if res.data:
              df_t = pd.DataFrame(res.data)
              dados_contexto += (
                  f"\n--- {titulo} ---\n{df_t.to_string(index=False)}\n"
              )
            else:
              dados_contexto += (
                  f"\n--- {titulo} ---\nSem registros para esta empresa.\n"
              )
          except Exception:
            pass

        return dados_contexto

      if "lista_mensagem" not in st.session_state:
        st.session_state["lista_mensagem"] = []

      # Componente da Esfera Laranja Holográfica e Reconhecimento por Voz
      voz_html = """
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <style>
                    .jarvis-container {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        background: radial-gradient(circle, #100500 0%, #050508 100%);
                        border: 1px solid rgba(255, 102, 0, 0.3);
                        border-radius: 12px;
                        padding: 20px;
                        box-shadow: 0 0 20px rgba(255, 102, 0, 0.2);
                        font-family: 'Courier New', monospace;
                        color: #ff6600;
                    }
                    canvas {
                        margin-bottom: 15px;
                    }
                    .btn-jarvis {
                        background-color: #ff6600;
                        color: #000;
                        border: none;
                        padding: 10px 20px;
                        font-weight: bold;
                        border-radius: 5px;
                        cursor: pointer;
                        box-shadow: 0 0 10px rgba(255, 102, 0, 0.5);
                        transition: 0.3s;
                    }
                    .btn-jarvis:hover {
                        background-color: #ffaa00;
                        box-shadow: 0 0 15px rgba(255, 170, 0, 0.8);
                    }
                    #status-voz {
                        margin-top: 10px;
                        font-size: 14px;
                        color: #ffaa00;
                    }
                </style>
            </head>
            <body>
                <div class="jarvis-container">
                    <canvas id="coreCanvas" width="200" height="200"></canvas>
                    <button class="btn-jarvis" onclick="iniciarEscuta()">🎙️ Falar com o ATLAS IA</button>
                    <div id="status-voz">Clique no botão e faça sua pergunta...</div>
                </div>

                <script>
                    const canvas = document.getElementById('coreCanvas');
                    const ctx = canvas.getContext('2d');
                    let angle = 0;

                    function desenharEsfera() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        
                        // Anel rotativo HUD
                        ctx.save();
                        ctx.translate(100, 100);
                        ctx.rotate(angle);
                        ctx.strokeStyle = '#ff6600';
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.arc(0, 0, 80, 0, Math.PI * 1.5);
                        ctx.stroke();
                        ctx.restore();

                        // Núcleo de Energia Laranja
                        let grad = ctx.createRadialGradient(100, 100, 5, 100, 100, 50);
                        grad.addColorStop(0, '#ffffff');
                        grad.addColorStop(0.4, '#ffaa00');
                        grad.addColorStop(1, '#ff3300');

                        ctx.fillStyle = grad;
                        ctx.beginPath();
                        ctx.arc(100, 100, 35 + Math.sin(angle * 5) * 3, 0, Math.PI * 2);
                        ctx.fill();

                        angle += 0.03;
                        requestAnimationFrame(desenharEsfera);
                    }
                    desenharEsfera();

                    function iniciarEscuta() {
                        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                        if (!SpeechRecognition) {
                            alert("Seu navegador não suporta reconhecimento de voz. Use o Google Chrome.");
                            return;
                        }
                        const recognition = new SpeechRecognition();
                        recognition.lang = 'pt-BR';
                        recognition.interimResults = false;

                        document.getElementById('status-voz').innerText = "Ouvindo... Fale agora!";
                        
                        recognition.start();

                        recognition.onresult = function(event) {
                            const textoFalado = event.results[0][0].transcript;
                            document.getElementById('status-voz').innerText = "Você disse: " + textoFalado;
                            
                            const streamlitInput = parent.document.querySelector('input[aria-label*="ATLAS"]');
                            if (streamlitInput) {
                                streamlitInput.value = textoFalado;
                                streamlitInput.dispatchEvent(new Event('input', { bubbles: true }));
                                streamlitInput.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true}));
                            }
                        };

                        recognition.onerror = function(event) {
                            document.getElementById('status-voz').innerText = "Erro no reconhecimento. Tente novamente.";
                        };
                    }

                    function falarResposta(texto) {
                        if ('speechSynthesis' in window) {
                            window.speechSynthesis.cancel();
                            const utterance = new SpeechSynthesisUtterance(texto);
                            utterance.lang = 'pt-BR';
                            utterance.rate = 1.1;
                            window.speechSynthesis.speak(utterance);
                        }
                    }
                </script>
            </body>
            </html>
            """

      components.html(voz_html, height=320)

      for mensagem in st.session_state["lista_mensagem"]:
        st.chat_message(mensagem["role"]).write(mensagem["content"])

      texto_user = st.chat_input(
          "Pergunte ao ATLAS (Por voz ou texto ex: Qual o estoque de produtos?)"
      )
      if texto_user:
        st.chat_message("user").write(texto_user)
        st.session_state["lista_mensagem"].append(
            {"role": "user", "content": texto_user}
        )

        if not client:
          texto_resposta_ia = (
              "Chave de API do Gemini não configurada nos segredos"
              " (`st.secrets`)."
          )
        else:
          try:
            dados_contexto = obter_contexto_completo_erp(empresa_atual)

            prompt_sistema = f"""
                        Você é o ATLAS IA, assistente inteligente corporativo e analista estratégico do ERP Capsule Sys.
                        Analise os dados reais do banco de dados da empresa "{empresa_atual}" abaixo para responder de forma precisa, executiva e concisa (ideal para ser lida em voz alta para o gestor).
                        
                        Dados Atuais e Completos do Sistema (Supabase):
                        {dados_contexto}
                        """

            historico_chat = [
                {"role": "user", "parts": [{"text": prompt_sistema}]}
            ]
            for msg in st.session_state["lista_mensagem"]:
              historico_chat.append({
                  "role": msg["role"],
                  "parts": [{"text": msg["content"]}],
              })

            resposta_ia = client.models.generate_content(
                model=modelo, contents=historico_chat
            )
            texto_resposta_ia = resposta_ia.text
          except Exception as e:
            try:
              resposta_ia = client.models.generate_content(
                  model=modelo, contents=texto_user
              )
              texto_resposta_ia = resposta_ia.text
            except Exception as err:
              texto_resposta_ia = f"Erro ao comunicar com a IA: {err}"

        st.chat_message("assistant").write(texto_resposta_ia)
        st.session_state["lista_mensagem"].append(
            {"role": "assistant", "content": texto_resposta_ia}
        )

        texto_voz_seguro = (
            texto_resposta_ia.replace('"', '\\"')
            .replace("\n", " ")
            .replace("\r", "")
        )
        components.html(
            f"""
            <script>
                if (parent && parent.window && parent.window.falarResposta) {{
                    parent.window.falarResposta("{texto_voz_seguro}");
                }}
            </script>
        """,
            height=0,
        )

    case "Contratos":
      st.header("Módulo de Contratos & Gestão de Projetos")
      escolha_contratos = st.radio(
          "Escolha uma opção:",
          [
              "Cadastro de Projeto",
              "Relatório Orçado vs. Realizado",
              "Emissão de Contratos",
              "Consulta & Download PDF",
          ],
          horizontal=True,
      )

      match escolha_contratos:
        case "Cadastro de Projeto":
          with st.form("form_projeto"):
            nome_projeto = st.text_input(
                "Nome do Projeto / Obra / Embarcação"
            )
            n_projeto = st.text_input("Número do Projeto / OS")
            valor_projeto = st.number_input(
                "Orçamento Previsto / Teto (R$)", min_value=0.0, step=1000.0
            )
            submit = st.form_submit_button("Salvar Projeto")
            if submit:
              try:
                supabase.table("projeto").insert({
                    "Descrição": nome_projeto,
                    "Número Projeto": n_projeto,
                    "Valor": float(valor_projeto),
                    "empresa_id": empresa_atual,
                }).execute()
                registrar_log(
                    usuario_atual, empresa_atual, "Projeto Criado", nome_projeto
                )
                st.success("Projeto Salvo com Sucesso!")
              except Exception as e:
                st.error(f"Erro ao salvar projeto: {e}")

        case "Relatório Orçado vs. Realizado":
          st.subheader(
              "Controladoria de Obras & Projetos: Orçado vs. Realizado"
          )
          try:
            res_proj = (
                supabase.table("projeto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_proj = pd.DataFrame(res_proj.data if res_proj.data else [])

            if not df_proj.empty:
              res_pedidos = (
                  supabase.table("vencedores")
                  .select("*")
                  .eq("empresa_id", empresa_atual)
                  .execute()
              )
              df_v = pd.DataFrame(res_pedidos.data if res_pedidos.data else [])

              relatorio_dados = []
              for idx, row in df_proj.iterrows():
                nome_p = str(row.get("Descrição", "N/D"))
                num_p = str(row.get("Número Projeto", ""))
                orcado = float(row.get("Valor", 0.0) or 0.0)

                realizado = 0.0
                if not df_v.empty:
                  pedidos_obra = (
                      df_v[
                          df_v["Produto"]
                          .astype(str)
                          .str.contains(nome_p, case=False, na=False)
                          | df_v.get("NumeroPedido", "")
                          .astype(str)
                          .str.contains(num_p, case=False, na=False)
                      ]
                      if "Produto" in df_v.columns
                      else pd.DataFrame()
                  )
                  if not pedidos_obra.empty:
                    realizado = (
                        pedidos_obra["Quantidade"].astype(float)
                        * pedidos_obra["Preço Cotado"].astype(float)
                    ).sum()

                saldo = orcado - realizado
                perc_gasto = (realizado / orcado * 100) if orcado > 0 else 0.0

                relatorio_dados.append({
                    "Obra / Projeto": nome_p,
                    "Cód. OS": num_p,
                    "Orçamento (R$)": orcado,
                    "Gasto Realizado (R$)": realizado,
                    "Saldo Disponível (R$)": saldo,
                    "% Comprometido": round(perc_gasto, 2),
                })

              df_rel = pd.DataFrame(relatorio_dados)

              tot_orc = df_rel["Orçamento (R$)"].sum()
              tot_real = df_rel["Gasto Realizado (R$)"].sum()

              m1, m2, m3 = st.columns(3)
              m1.metric("Total Orçado (Projetos)", f"R$ {tot_orc:,.2f}")
              m2.metric("Total Realizado em Compras", f"R$ {tot_real:,.2f}")
              m3.metric("Saldo Global", f"R$ {(tot_orc - tot_real):,.2f}")

              st.divider()
              st.dataframe(df_rel, use_container_width=True)
              st.bar_chart(
                  df_rel.set_index("Obra / Projeto")[
                      ["Orçamento (R$)", "Gasto Realizado (R$)"]
                  ]
              )
            else:
              st.info("Nenhum projeto cadastrado para análise.")
          except Exception as e:
            st.error(f"Erro ao consolidar relatório: {e}")

        case "Emissão de Contratos":
          try:
            res_p = (
                supabase.table("projeto")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            res_f = (
                supabase.table("fornecedor")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )

            df_contrato_projeto = pd.DataFrame(
                res_p.data if res_p.data else []
            )
            df_fornecedor_contrato = pd.DataFrame(
                res_f.data if res_f.data else []
            )

            proj_lista = (
                df_contrato_projeto["Descrição"].tolist()
                if not df_contrato_projeto.empty
                and "Descrição" in df_contrato_projeto.columns
                else []
            )
            forn_lista = (
                df_fornecedor_contrato["Nome Fornecedor"].tolist()
                if not df_fornecedor_contrato.empty
                and "Nome Fornecedor" in df_fornecedor_contrato.columns
                else []
            )

            contrato_projeto = st.selectbox("Projeto", proj_lista)
            empresa_contratante = st.selectbox(
                "Empresa Contratante", [empresa_atual]
            )
            contrato_fornecedor = st.selectbox(
                "Escolha o Fornecedor", forn_lista
            )
            contrato_objeto = st.text_area("Objeto do Contrato")
            valor_contrato = st.number_input(
                "Valor Contrato (R$)", min_value=0.0, step=100.0
            )

            if st.button("Salvar Contrato"):
              supabase.table("contrato").insert({
                  "Empresa Contratante": str(empresa_contratante),
                  "Fornecedor": str(contrato_fornecedor),
                  "Objeto": str(contrato_objeto),
                  "Valor": float(valor_contrato),
                  "Projeto": str(contrato_projeto),
                  "empresa_id": empresa_atual,
              }).execute()
              registrar_log(
                  usuario_atual,
                  empresa_atual,
                  "Contrato Salvo",
                  f"Projeto: {contrato_projeto} | Fornecedor:"
                  f" {contrato_fornecedor}",
              )
              st.success("Contrato Salvo com Sucesso!")
          except Exception as e:
            st.error(f"Erro nos contratos: {e}")

        case "Consulta & Download PDF":
          st.subheader("Consultar e Exportar Contratos em PDF")
          try:
            res_ct = (
                supabase.table("contrato")
                .select("*")
                .eq("empresa_id", empresa_atual)
                .execute()
            )
            df_contratos = pd.DataFrame(res_ct.data if res_ct.data else [])

            if not df_contratos.empty:
              df_contratos["Label"] = (
                  "ID "
                  + df_contratos["id"].astype(str)
                  + " - "
                  + df_contratos.get("Projeto", "N/D").astype(str)
                  + " ("
                  + df_contratos.get("Fornecedor", "N/D").astype(str)
                  + ")"
              )
              contrato_sel_label = st.selectbox(
                  "Selecione o Contrato", df_contratos["Label"].unique().tolist()
              )

              id_contrato_sel = int(
                  contrato_sel_label.split(" - ")[0].replace("ID ", "").strip()
              )
              row_c = df_contratos[
                  df_contratos["id"] == id_contrato_sel
              ].iloc[0]

              st.write("---")
              col_info1, col_info2 = st.columns(2)
              with col_info1:
                st.write(
                    "**Empresa Contratante:**"
                    f" {row_c.get('Empresa Contratante', empresa_atual)}"
                )
                st.write(
                    "**Fornecedor / Contratado:**"
                    f" {row_c.get('Fornecedor', 'N/D')}"
                )
                st.write(
                    f"**Projeto / Obra:** {row_c.get('Projeto', 'N/D')}"
                )
              with col_info2:
                vl_c = float(row_c.get("Valor", 0.0) or 0.0)
                st.write(f"**Valor do Contrato:** R$ {vl_c:,.2f}")
                st.write(f"**ID do Registro:** {row_c.get('id')}")

              st.write("**Objeto do Contrato:**")
              st.info(row_c.get("Objeto", "Sem objeto cadastrado."))

              buffer_contrato = io.BytesIO()
              doc_c = SimpleDocTemplate(
                  buffer_contrato,
                  pagesize=A4,
                  rightMargin=30,
                  leftMargin=30,
                  topMargin=30,
                  bottomMargin=30,
              )
              elementos_c = []

              estilos_c = getSampleStyleSheet()
              estilo_normal_c = estilos_c["Normal"]
              estilo_normal_c.fontSize = 9
              estilo_normal_c.leading = 12

              if os.path.exists("capsuleSys.png"):
                img_rl_c = RLImage("capsuleSys.png", width=120, height=45)
                txt_header = Paragraph(
                    f"<b>{row_c.get('Empresa Contratante', empresa_atual)}</b><br/>"
                    "<font size=12 color='#003366'><b>INSTRUMENTO PARTICULAR DE"
                    " CONTRATO</b></font><br/>DATA DE EMISSÃO:"
                    f" {datetime.now().strftime('%d/%m/%Y')}",
                    estilo_normal_c,
                )
                tbl_head = Table(
                    [[txt_header, img_rl_c]], colWidths=[380, 150]
                )
                tbl_head.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ]))
                elementos_c.append(tbl_head)
              else:
                txt_header = (
                    f"<b>{row_c.get('Empresa Contratante', empresa_atual)}</b><br/>"
                    "<font size=12 color='#003366'><b>INSTRUMENTO PARTICULAR DE"
                    " CONTRATO</b></font><br/>DATA DE EMISSÃO:"
                    f" {datetime.now().strftime('%d/%m/%Y')}"
                )
                elementos_c.append(Paragraph(txt_header, estilo_normal_c))

              elementos_c.append(Spacer(1, 15))

              dados_partes = [
                  [
                      "CONTRATANTE",
                      str(row_c.get("Empresa Contratante", empresa_atual)),
                  ],
                  [
                      "CONTRATADO / FORNECEDOR",
                      str(row_c.get("Fornecedor", "N/D")),
                  ],
                  ["PROJETO / OBRA", str(row_c.get("Projeto", "N/D"))],
                  ["VALOR TOTAL", f"R$ {vl_c:,.2f}"],
              ]
              tbl_partes = Table(dados_partes, colWidths=[160, 340])
              tbl_partes.setStyle(TableStyle([
                  ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
                  ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                  ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                  ("FONTSIZE", (0, 0), (-1, -1), 8),
              ]))
              elementos_c.append(tbl_partes)
              elementos_c.append(Spacer(1, 15))

              elementos_c.append(
                  Paragraph("<b>OBJETO DO CONTRATO:</b>", estilo_normal_c)
              )
              elementos_c.append(Spacer(1, 5))
              elementos_c.append(
                  Paragraph(
                      str(
                          row_c.get("Objeto", "Sem objeto cadastrado.")
                      ).replace("\n", "<br/>"),
                      estilo_normal_c,
                  )
              )

              elementos_c.append(Spacer(1, 40))

              dados_ass = [
                  [
                      "_________________________________________",
                      "_________________________________________",
                  ],
                  [
                      (
                          "CONTRATANTE:"
                          f" {row_c.get('Empresa Contratante', empresa_atual)}"
                      ),
                      f"CONTRATADO: {row_c.get('Fornecedor', 'N/D')}",
                  ],
              ]
              tbl_ass = Table(dados_ass, colWidths=[250, 250])
              tbl_ass.setStyle(TableStyle([
                  ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                  ("FONTSIZE", (0, 0), (-1, -1), 8),
              ]))
              elementos_c.append(tbl_ass)

              doc_c.build(elementos_c)
              buffer_contrato.seek(0)

              st.download_button(
                  label="Baixar Contrato (PDF)",
                  data=buffer_contrato,
                  file_name=(
                      f"contrato_{id_contrato_sel}_{row_c.get('Fornecedor', 'fornecedor')}.pdf"
                  ),
                  mime="application/pdf",
              )

              st.divider()
              st.subheader("Todos os Contratos Cadastrados")
              st.dataframe(
                  df_contratos[[
                      "id",
                      "Empresa Contratante",
                      "Fornecedor",
                      "Projeto",
                      "Valor",
                      "Objeto",
                  ]],
                  use_container_width=True,
              )

            else:
              st.info("Nenhum contrato cadastrado para consulta.")
          except Exception as e:
            st.error(f"Erro ao consultar contratos: {e}")

    case "Desconectar":
      registrar_log(
          usuario_atual, empresa_atual, "Logout", "Sessão encerrada"
      )
      st.session_state["logado"] = False
      st.rerun()