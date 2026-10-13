import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Configuração da página para ocupar a tela cheia (como o min-h-screen da imagem)
st.set_page_config(
    page_title="Radar de Concorrência - Inteligência Comercial",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CUSTOMIZADA (Para aproximar o Streamlit ao visual clean do Tailwind) ---
st.markdown("""
    <style>
    /* Fundo suave baseado no gradiente do Tailwind da imagem */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 50%, #ecfeff 100%);
    }
    /* Estilização dos blocos (Cards) */
    .card-concorrente {
        background-color: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 16px;
    }
    .preco-principal {
        font-size: 24px;
        font-weight: bold;
        color: #1e293b;
    }
    .preco-concorrente-baixo {
        color: #dc2626; /* Vermelho se o concorrente está mais barato */
        font-weight: bold;
    }
    .preco-concorrente-alto {
        color: #16a34a; /* Verde se o concorrente está mais caro */
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIMULAÇÃO DE DADOS (Simulando o que viria da API/Raspagem do Menor Preço) ---
@st.cache_data
def carregar_dados_concorrencia():
    # Produtos de exemplo para o mercado
    produtos = [
        {"id": 1, "descricao": "Leite UHT Integral 1L", "seu_preco": 4.59, "categoria": "Mercearia Doce"},
        {"id": 2, "descricao": "Arroz Agulhinha Tipo 1 5kg", "seu_preco": 24.90, "categoria": "Mercearia Salgada"},
        {"id": 3, "descricao": "Óleo de Soja 900ml", "seu_preco": 6.29, "categoria": "Mercearia Salgada"},
        {"id": 4, "descricao": "Café Torrado e Moído 500g", "seu_preco": 16.80, "categoria": "Mercearia Doce"},
    ]
    
    # Registros capturados no "Menor Preço" para esses produtos
    concorrentes = [
        {"id_prod": 1, "mercado": "Supermercado Alfa (A 1.2km)", "preco": 4.39, "data": "Hoje"},
        {"id_prod": 1, "mercado": "Hiper Beta (A 3.5km)", "preco": 4.65, "data": "Ontem"},
        {"id_prod": 2, "mercado": "Supermercado Alfa (A 1.2km)", "preco": 25.50, "data": "Hoje"},
        {"id_prod": 2, "mercado": "Mercado Gamma (A 0.8km)", "preco": 23.95, "data": "Hoje"},
        {"id_prod": 3, "mercado": "Hiper Beta (A 3.5km)", "preco": 6.19, "data": "Hoje"},
        {"id_prod": 4, "mercado": "Mercado Gamma (A 0.8km)", "preco": 17.20, "data": "Ontem"},
    ]
    return pd.DataFrame(produtos), pd.DataFrame(concorrentes)

df_produtos, df_concorrentes = carregar_dados_concorrencia()

# --- HEADER (Sticky no topo) ---
st.title("🎯 Radar Menor Preço - Monitoramento de Concorrência")
st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} — Dados baseados nas últimas NF-e emitidas na região.")
st.write("---")

# --- DISTRIBUIÇÃO EM COLUNAS (Espelhando a regra xl:grid-cols-[360px_1fr] da imagem) ---
# No Streamlit, usamos colunas com proporções para dar o peso correto na tela
col_esquerda, col_direita = st.columns([1, 2.5])

# === COLUNA ESQUERDA: FILTROS E SELEÇÃO DE PRODUTO (Painel de 360px) ===
with col_esquerda:
    st.markdown('<div class="card-concorrente">', unsafe_allow_html=True)
    st.markdown("### 🔍 Filtrar Produto")
    
    categoria_sel = st.selectbox("Filtrar por Categoria", ["Todas"] + list(df_produtos["categoria"].unique()))
    
    if categoria_sel != "Todas":
        produtos_filtrados = df_produtos[df_produtos["categoria"] == categoria_sel]
    else:
        produtos_filtrados = df_produtos
        
    lista_produtos_nomes = produtos_filtrados["descricao"].tolist()
    produto_selecionado = st.selectbox("Selecione o Item para Auditoria:", lista_produtos_nomes)
    
    # Detalhes do Produto Selecionado
    info_prod = df_produtos[df_produtos["descricao"] == produto_selecionado].iloc[0]
    
    st.markdown("---")
    st.markdown(f"**Seu Preço Atual:**")
    st.markdown(f'<p class="preco-principal">R$ {info_prod["seu_preco"]:.2f}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# === COLUNA DIREITA: ANÁLISE DE MERCADO E CONCORRENTES COMPATÍVEIS ===
with col_direita:
    st.markdown(f"### Análise de Competitividade: *{produto_selecionado}*")
    
    # Filtrando os concorrentes que venderam o mesmo produto
    concorrentes_do_item = df_concorrentes[df_concorrentes["id_prod"] == info_prod["id"]]
    
    if not concorrentes_do_item.empty:
        # Criando os 3 Cards Verticais (Espelhando as sub-divs com space-y-4 da imagem)
        for _, row in concorrentes_do_item.iterrows():
            diferenca = row['preco'] - info_prod['seu_preco']
            porcentagem = (diferenca / info_prod['seu_preco']) * 100
            
            # Define a cor e o texto do status baseado no preço do concorrente
            if diferenca < 0:
                status_html = f'<span class="preco-concorrente-baixo">Alerta: Concorrente está {abs(porcentagem):.1f}% mais BARATO</span>'
            else:
                status_html = f'<span class="preco-concorrente-alto">Seguro: Concorrente está {abs(porcentagem):.1f}% mais CARO</span>'
                
            # Estrutura do Card em HTML puro para manter o design elegante
            st.markdown(f"""
                <div class="card-concorrente">
                    <table style="width:100%; border:none; border-collapse:collapse;">
                        <tr style="background:none;">
                            <td style="width:70%; border:none; padding:0;">
                                <strong style="font-size:16px; color:#0f172a;">{row['mercado']}</strong><br>
                                <small style="color:#64748b;">Nota emitida: {row['data']}</small>
                            </td>
                            <td style="text-align:right; border:none; padding:0;">
                                <span style="font-size:14px; color:#64748b;">Preço Praticado</span><br>
                                <strong style="font-size:18px; color:#0f172a;">R$ {row['preco']:.2f}</strong>
                            </td>
                        </tr>
                    </table>
                    <div style="margin-top: 10px; font-size:13px;">
                        {status_html}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        # Uma tabela complementar abaixo dos cards para auditoria em lote
        with st.expander("📊 Ver visão consolidada em tabela"):
            st.dataframe(
                concorrentes_do_item.rename(columns={"mercado": "Estabelecimento", "preco": "Preço Concorrente", "data": "Última NF-e"}), 
                use_container_width=True, 
                hide_index=True
            )
    else:
        st.info("Nenhuma venda desse produto foi capturada pelo 'Menor Preço' na sua região nas últimas 48 horas.")