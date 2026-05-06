import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Reajuste Contratual - IGP-M", layout="centered")

st.title("📊 Reajuste Contratual pelo IGP-M")

# ================================
# BUSCAR IGP-M (BANCO CENTRAL)
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
# FUNÇÃO DE CÁLCULO (ESTILO BCB)
# ================================
def calcular_reajuste(df_filtrado, valor_inicial):
    fator = 1.0

    for _, row in df_filtrado.iterrows():
        fator *= (1 + row["valor"] / 100)

    valor_final = valor_inicial * fator
    return valor_final, fator

# ================================
# GERAR PDF
# ================================
def gerar_pdf(
    contrato,
    contratante,
    contratada,
    objeto,
    valor,
    valor_corrigido,
    fator,
    df_filtrado,
    data_inicio,
    data_fim,
    responsavel
):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elementos = []

    valor_reajuste = valor_corrigido - valor

    elementos.append(Paragraph("<b>RELATÓRIO DE REAJUSTE CONTRATUAL</b>", styles["Title"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>1. IDENTIFICAÇÃO DO CONTRATO</b>", styles["Heading2"]))
    elementos.append(Paragraph(f"Contrato nº: {contrato}", styles["Normal"]))
    elementos.append(Paragraph(f"Contratante: {contratante}", styles["Normal"]))
    elementos.append(Paragraph(f"Contratada: {contratada}", styles["Normal"]))
    elementos.append(Paragraph(f"Objeto: {objeto}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>2. FUNDAMENTAÇÃO LEGAL</b>", styles["Heading2"]))
    elementos.append(Paragraph(
        "Reajuste fundamentado na Lei nº 14.133/2021 para manutenção do equilíbrio econômico-financeiro.",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>3. ÍNDICE DE REAJUSTE</b>", styles["Heading2"]))
    elementos.append(Paragraph("Índice utilizado: IGP-M (Banco Central)", styles["Normal"]))
    elementos.append(Paragraph(
        f"Período: {data_inicio.strftime('%m/%Y')} a {data_fim.strftime('%m/%Y')}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>4. MEMÓRIA DE CÁLCULO</b>", styles["Heading2"]))
    elementos.append(Paragraph(f"Valor inicial: R$ {valor:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Valor corrigido: R$ {valor_corrigido:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Reajuste: R$ {valor_reajuste:,.2f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    dados = [["Mês/Ano", "IGP-M (%)"]]

    for _, row in df_filtrado.iterrows():
        dados.append([
            row["data"].strftime("%m/%Y"),
            f"{row['valor']:.2f}"
        ])

    tabela = Table(dados)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("<b>5. CONCLUSÃO</b>", styles["Heading2"]))
    elementos.append(Paragraph(
        "Recomenda-se o reajuste para manter o equilíbrio econômico-financeiro.",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph(
        f"Data: {datetime.now().strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph(f"Responsável: {responsavel}", styles["Normal"]))

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

    mes_inicio = pd.to_datetime(data_inicio).to_period("M")
    mes_fim = pd.to_datetime(data_fim).to_period("M")

    df_filtrado = df_indices[
        (df_indices["mes"] >= mes_inicio) &
        (df_indices["mes"] <= mes_fim)
    ].copy()

    if df_filtrado.empty:
        st.error("Sem dados para o período.")
        st.stop()

    valor_corrigido, fator = calcular_reajuste(df_filtrado, valor)

    st.success("Reajuste calculado com sucesso!")
    st.metric("Valor corrigido", f"R$ {valor_corrigido:,.2f}")

    # TABELA ESTILO CALCULADORA DO CIDADÃO
    df_calc = df_filtrado.copy()
    df_calc["fator_mes"] = 1 + (df_calc["valor"] / 100)
    df_calc["acumulado"] = df_calc["fator_mes"].cumprod()
    df_calc["valor_corrigido"] = valor * df_calc["acumulado"]

    st.subheader("📊 Evolução do Reajuste")
    st.dataframe(df_calc[["data", "valor", "valor_corrigido"]])

    # PDF
    pdf = gerar_pdf(
        contrato,
        contratante,
        contratada,
        objeto,
        valor,
        valor_corrigido,
        fator,
        df_filtrado,
        data_inicio,
        data_fim,
        responsavel
    )

    st.download_button(
        "📄 Baixar PDF",
        data=pdf,
        file_name="reajuste_contratual.pdf",
        mime="application/pdf"
    )
