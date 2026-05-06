import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Reajuste Contratual - IGP-M", layout="centered")

st.title("📊 Reajuste Contratual pelo IGP-M")

# ================================
# BUSCAR IGP-M
# ================================
@st.cache_data
def buscar_igpm():
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.189/dados?formato=json"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        dados = response.json()
    except Exception as e:
        st.error(f"Erro ao acessar Banco Central: {e}")
        return None

    if not dados:
        return None

    df = pd.DataFrame(dados)

    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"].str.replace(",", "."), errors="coerce")

    df = df.dropna()
    df = df.sort_values("data")
    df["mes"] = df["data"].dt.to_period("M")

    return df


df_indices = buscar_igpm()

if df_indices is None:
    st.error("Erro ao carregar IGP-M.")
    st.stop()

# ================================
# CÁLCULO PADRÃO BCB
# ================================
def calcular_reajuste_bcb(df_filtrado, valor_inicial):
    valor = Decimal(str(valor_inicial)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    historico = []

    for _, row in df_filtrado.iterrows():
        indice = Decimal(str(row["valor"])) / Decimal("100")
        fator = Decimal("1") + indice

        valor = (valor * fator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        historico.append({
            "mes_ano": row["data"].strftime("%m/%Y"),
            "indice (%)": float(row["valor"]),
            "valor_corrigido": float(valor)
        })

    valor = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return float(valor), historico

# ================================
# GERAR PDF
# ================================
def gerar_pdf(contrato, contratante, contratada, objeto, valor, valor_corrigido,
              df_filtrado, data_inicio, data_fim, responsavel):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elementos = []

    valor_reajuste = valor_corrigido - valor

    elementos.append(Paragraph("<b>RELATÓRIO DE REAJUSTE CONTRATUAL</b>", styles["Title"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>1. IDENTIFICAÇÃO</b>", styles["Heading2"]))
    elementos.append(Paragraph(f"Contrato nº: {contrato}", styles["Normal"]))
    elementos.append(Paragraph(f"Contratante: {contratante}", styles["Normal"]))
    elementos.append(Paragraph(f"Contratada: {contratada}", styles["Normal"]))
    elementos.append(Paragraph(f"Objeto: {objeto}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>2. FUNDAMENTAÇÃO</b>", styles["Heading2"]))
    elementos.append(Paragraph("Lei nº 14.133/2021.", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>3. MEMÓRIA DE CÁLCULO</b>", styles["Heading2"]))
    elementos.append(Paragraph(f"Valor inicial: R$ {valor:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Valor corrigido: R$ {valor_corrigido:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Reajuste: R$ {valor_reajuste:,.2f}", styles["Normal"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ================================
# FORMULÁRIO
# ================================
st.subheader("📄 Dados do Contrato")

contrato = st.text_input("Contrato nº")
contratante = st.text_input("Contratante")
contratada = st.text_input("Contratada")
objeto = st.text_area("Objeto")
responsavel = st.text_input("Responsável")

st.subheader("💰 Dados Financeiros")

valor = st.number_input("Valor inicial (R$)", min_value=0.0, value=1000.0)

col1, col2 = st.columns(2)

with col1:
    data_inicio = st.date_input("Data inicial")

with col2:
    data_fim = st.date_input("Data final")

# ================================
# CÁLCULO
# ================================
if st.button("Calcular Reajuste"):

    if data_inicio >= data_fim:
        st.warning("Data final deve ser maior.")
        st.stop()

    # 🔥 Trabalhar só mês/ano
    data_inicio_mes = pd.to_datetime(data_inicio).replace(day=1)
    data_fim_mes = pd.to_datetime(data_fim).replace(day=1)

    mes_inicio = pd.Period(data_inicio_mes, freq="M")
    mes_fim = pd.Period(data_fim_mes, freq="M")

    df_filtrado = df_indices[
        (df_indices["mes"] > mes_inicio) &
        (df_indices["mes"] <= mes_fim)
    ].copy()

    df_filtrado = df_filtrado.sort_values("mes")

    if df_filtrado.empty:
        st.error("Sem dados para o período.")
        st.stop()

    valor_corrigido, historico = calcular_reajuste_bcb(df_filtrado, valor)

    st.success("Reajuste calculado com sucesso!")
    st.metric("Valor corrigido", f"R$ {valor_corrigido:,.2f}")

    # Tabela evolução
    df_calc = pd.DataFrame(historico)
    st.subheader("📊 Evolução do Reajuste")
    st.dataframe(df_calc)

    # =============================
    # 🔍 COMPARAÇÃO COM BCB
    # =============================
    st.subheader("🔍 Comparação com Banco Central")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Seu Sistema", f"R$ {valor_corrigido:,.2f}")

    with col2:
        valor_bcb = st.number_input("Valor do Banco Central", min_value=0.0, format="%.2f")

    if valor_bcb > 0:
        diferenca = round(valor_corrigido - valor_bcb, 2)

        if abs(diferenca) < 0.01:
            st.success("✅ Valores idênticos ao Banco Central")
        else:
            st.warning(f"⚠️ Diferença: R$ {diferenca:,.2f}")

        df_comp = pd.DataFrame({
            "Fonte": ["Seu Sistema", "Banco Central"],
            "Valor (R$)": [valor_corrigido, valor_bcb]
        })

        st.table(df_comp)

    # PDF
    pdf = gerar_pdf(
        contrato, contratante, contratada, objeto,
        valor, valor_corrigido,
        df_filtrado, data_inicio_mes, data_fim_mes, responsavel
    )

    st.download_button(
        "📄 Baixar PDF",
        data=pdf,
        file_name="reajuste_contratual.pdf",
        mime="application/pdf"
    )
