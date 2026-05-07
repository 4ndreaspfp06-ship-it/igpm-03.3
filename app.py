import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(
    page_title="Reajuste Contratual - IGP-M",
    layout="centered"
)

st.title("📊 Reajuste Contratual pelo IGP-M")

# ======================================================
# BUSCAR IGP-M
# ======================================================
@st.cache_data
def buscar_igpm():

    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.189/dados?formato=json"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    df = pd.DataFrame(response.json())

    df["data"] = pd.to_datetime(
        df["data"],
        dayfirst=True
    )

    df["valor"] = (
        df["valor"]
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df["mes"] = df["data"].dt.strftime("%m/%Y")

    return df


df_indices = buscar_igpm()

# ======================================================
# PDF
# ======================================================
def gerar_pdf(
    contrato,
    contratante,
    contratada,
    objeto,
    valor,
    valor_corrigido,
    percentual,
    df_filtrado,
    mes_inicio,
    mes_fim,
    responsavel
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elementos = []

    reajuste = valor_corrigido - valor

    # TÍTULO
    elementos.append(
        Paragraph(
            "<b>RELATÓRIO DE REAJUSTE CONTRATUAL</b>",
            styles["Title"]
        )
    )

    elementos.append(Spacer(1, 20))

    # IDENTIFICAÇÃO
    elementos.append(
        Paragraph(
            "<b>1. IDENTIFICAÇÃO DO CONTRATO</b>",
            styles["Heading2"]
        )
    )

    elementos.append(
        Paragraph(f"Contrato nº: {contrato}", styles["Normal"])
    )

    elementos.append(
        Paragraph(f"Contratante: {contratante}", styles["Normal"])
    )

    elementos.append(
        Paragraph(f"Contratada: {contratada}", styles["Normal"])
    )

    elementos.append(
        Paragraph(f"Objeto: {objeto}", styles["Normal"])
    )

    elementos.append(Spacer(1, 15))

    # FUNDAMENTAÇÃO
    elementos.append(
        Paragraph(
            "<b>2. FUNDAMENTAÇÃO LEGAL</b>",
            styles["Heading2"]
        )
    )

    texto = (
        "O presente reajuste contratual está fundamentado "
        "na Lei nº 14.133/2021, visando à manutenção "
        "do equilíbrio econômico-financeiro do contrato."
    )

    elementos.append(
        Paragraph(texto, styles["Normal"])
    )

    elementos.append(Spacer(1, 15))

    # CÁLCULO
    elementos.append(
        Paragraph(
            "<b>3. MEMÓRIA DE CÁLCULO</b>",
            styles["Heading2"]
        )
    )

    elementos.append(
        Paragraph(
            f"Período: {mes_inicio} até {mes_fim}",
            styles["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"Valor inicial: R$ {valor:,.2f}",
            styles["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"Percentual acumulado: {percentual:.4f}%",
            styles["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"Valor reajustado: R$ {valor_corrigido:,.2f}",
            styles["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"Valor do reajuste: R$ {reajuste:,.2f}",
            styles["Normal"]
        )
    )

    elementos.append(Spacer(1, 15))

    # TABELA
    dados = [["Mês/Ano", "IGP-M (%)"]]

    for _, row in df_filtrado.iterrows():

        dados.append([
            row["mes"],
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

    # ASSINATURA
    elementos.append(
        Paragraph(
            f"Responsável pelo cálculo: {responsavel}",
            styles["Normal"]
        )
    )

    elementos.append(Spacer(1, 30))

    elementos.append(
        Paragraph(
            "Assinatura: __________________________",
            styles["Normal"]
        )
    )

    doc.build(elementos)

    buffer.seek(0)

    return buffer


# ======================================================
# FORMULÁRIO
# ======================================================
st.subheader("📄 Dados do Contrato")

contrato = st.text_input("Contrato nº")

contratante = st.text_input("Contratante")

contratada = st.text_input("Contratada")

objeto = st.text_area("Objeto")

responsavel = st.text_input("Responsável pelo cálculo")

st.subheader("💰 Dados Financeiros")

valor = st.number_input(
    "Valor inicial (R$)",
    min_value=0.0,
    value=1000.0
)

# ======================================================
# MÊS/ANO
# ======================================================
meses = df_indices["mes"].tolist()

col1, col2 = st.columns(2)

with col1:

    mes_inicio = st.selectbox(
        "Mês/Ano Inicial",
        meses,
        index=max(len(meses)-13, 0)
    )

with col2:

    mes_fim = st.selectbox(
        "Mês/Ano Final",
        meses,
        index=len(meses)-1
    )

# ======================================================
# CALCULAR
# ======================================================
if st.button("Calcular Reajuste"):

    data_inicio = datetime.strptime(mes_inicio, "%m/%Y")
    data_fim = datetime.strptime(mes_fim, "%m/%Y")

    if data_inicio >= data_fim:

        st.warning(
            "O período final deve ser maior."
        )

        st.stop()

    # FILTRO CORRETO
    df_filtrado = df_indices[
        (df_indices["data"] >= data_inicio) &
        (df_indices["data"] <= data_fim)
    ].copy()

    if df_filtrado.empty:

        st.error("Não existem índices no período.")

        st.stop()

    # CÁLCULO ACUMULADO CORRETO
    fator = 1

    for indice in df_filtrado["valor"]:

        fator *= (1 + indice / 100)

    percentual = (fator - 1) * 100

    valor_corrigido = valor * fator

    st.success("Reajuste calculado com sucesso.")

    st.metric(
        "Percentual acumulado",
        f"{percentual:.4f}%"
    )

    st.metric(
        "Valor reajustado",
        f"R$ {valor_corrigido:,.2f}"
    )

    # TABELA
    st.subheader("📑 Índices Utilizados")

    st.dataframe(
        df_filtrado[["mes", "valor"]]
        .rename(columns={
            "mes": "Mês/Ano",
            "valor": "IGP-M (%)"
        }),
        use_container_width=True
    )

    # PDF
    pdf = gerar_pdf(
        contrato,
        contratante,
        contratada,
        objeto,
        valor,
        valor_corrigido,
        percentual,
        df_filtrado,
        mes_inicio,
        mes_fim,
        responsavel
    )

    st.download_button(
        "📄 Baixar Relatório PDF",
        data=pdf,
        file_name=f"reajuste_igpm_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
