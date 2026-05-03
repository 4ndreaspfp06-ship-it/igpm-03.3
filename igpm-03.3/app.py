import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="IGP-M Online", layout="wide")

st.title("📊 Calculadora de Correção pelo IGP-M (Automática)")

# ================================
# 1. FUNÇÃO PARA BUSCAR DADOS ONLINE
# ================================
@st.cache_data
def carregar_igpm():
    # API do Banco Central (série 189 - IGP-M)
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.189/dados?formato=json"
    
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data)
    
    # Ajustar colunas
    df.rename(columns={"data": "mes", "valor": "igpm"}, inplace=True)
    
    # Converter tipos
    df["mes"] = pd.to_datetime(df["mes"], dayfirst=True)
    df["igpm"] = pd.to_numeric(df["igpm"])
    
    return df


# ================================
# 2. CARREGAR BASE
# ================================
df_indices = carregar_igpm()

st.success("✅ Índices carregados automaticamente")

# ================================
# 3. ENTRADAS DO USUÁRIO
# ================================
col1, col2 = st.columns(2)

with col1:
    data_inicio = st.date_input("Data Inicial")

with col2:
    data_fim = st.date_input("Data Final")

valor = st.number_input("Valor Inicial (R$)", min_value=0.0, value=1000.0)

# ================================
# 4. FILTRO E CÁLCULO
# ================================
if data_inicio and data_fim:

    df_filtrado = df_indices[
        (df_indices["mes"] >= pd.to_datetime(data_inicio)) &
        (df_indices["mes"] <= pd.to_datetime(data_fim))
    ]

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum índice encontrado no período.")
    else:
        st.write("📅 Índices utilizados:", df_filtrado)

        # Cálculo acumulado
        fator = (1 + df_filtrado["igpm"] / 100).prod()
        valor_corrigido = valor * fator

        # ================================
        # 5. RESULTADO
        # ================================
        st.success(f"💰 Valor corrigido: R$ {valor_corrigido:,.2f}")

        # Mostrar variação total
        variacao = (fator - 1) * 100
        st.info(f"📈 Variação no período: {variacao:.2f}%")

        # ================================
        # 6. GRÁFICO
        # ================================
        st.line_chart(df_filtrado.set_index("mes")["igpm"])

else:
    st.info("📅 Informe as datas para calcular.")