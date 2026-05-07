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

# ======================================================
# CONFIGURAÇÃO
# ======================================================

st.set_page_config(
    page_title="Reajuste Contratual - IGP-M",
    layout="centered"
)

st.title("📊 Reajuste Contratual pelo IGP-M")

# ======================================================
# BUSCAR IGP-M DO BANCO CENTRAL
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
        .round(2)
    )

    df = df.sort_values("data")

    df["mes"] = df["data"].dt.strftime("%m/%Y")

    return df


df_indices = buscar_igpm()

# ======================================================
# GERAR PDF
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
    responsavel
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elementos = []

    reajuste = round(valor_corrigido - valor, 2)

    # ==================================================
    # TÍTULO
    # ==================================================

    elementos.append(
        Paragraph(
            "<b>RELATÓRIO DE REAJUSTE CONTRATUAL</b>",
            styles["Title"]
        )
    )

    elementos.append(Spacer(1, 20))

    # ==================================================
    # IDENTIFICAÇÃO
    # ==================================================

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

    # ==================================================
    # FUNDAMENTAÇÃO
    # ==================================================

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

    # ==================================================
    # MEMÓRIA DE CÁLCULO
    # ==================================================

    elementos.append(
        Paragraph(
            "<b>3. MEMÓRIA DE CÁLCULO</b>",
            styles["Heading2"]
        )
    )

    elementos.append(
        Paragraph(
            f"Período considerado: "
            f"{df_filtrado.iloc[0]['mes']} até "
            f"{df_filtrado.iloc[-1]['mes']}",
            styles["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            "Cálculo realizado considerando os "
            "últimos 12 meses acumulados do IGP-M.",
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
            f"Percentual acumulado: {percentual:.2f}%",
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

    # ==================================================
    # TABELA
    # ==================================================

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

    # ==================================================
    # CONCLUSÃO
    # ==================================================

    elementos.append(
        Paragraph(
            "<b>4. CONCLUSÃO</b>",
            styles["Heading2"]
        )
    )

    elementos.append(
        Paragraph(
            "Após aplicação do índice acumulado "
            "dos últimos 12 meses do IGP-M, "
            "verifica-se a necessidade de atualização "
            "do valor contratual.",
            styles["Normal"]
        )
    )

    elementos.append(Spacer(1, 25))

    # ==================================================
    # ASSINATURA
    # ==================================================

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

# ======================================================
# DADOS FINANCEIROS
# ======================================================

st.subheader("💰 Dados Financeiros")

valor = st.number_input(
    "Valor inicial (R$)",
    min_value=0.0,
    value=1000.00,
    step=100.00
)

# ======================================================
# SELEÇÃO MÊS/ANO
# ======================================================

meses = df_indices["mes"].tolist()

mes_referencia = st.selectbox(
    "Mês/Ano de referência do reajuste",
    meses,
    index=len(meses)-1
)

# ======================================================
# CÁLCULO
# ======================================================

if st.button("📊 Calcular Reajuste"):

    data_referencia = datetime.strptime(
        mes_referencia,
        "%m/%Y"
    )

    # ==================================================
    # PEGAR ÚLTIMOS 12 MESES
    # ==================================================

    df_filtrado = df_indices[
        df_indices["data"] <= data_referencia
    ].tail(12).copy()

    if len(df_filtrado) < 12:

        st.error(
            "Não existem 12 meses completos disponíveis."
        )

        st.stop()

    # ==================================================
    # CÁLCULO ACUMULADO
    # ==================================================

    fator = 1

    for indice in df_filtrado["valor"]:

        indice = round(indice, 2)

        fator *= (1 + indice / 100)

    percentual = round(
        (fator - 1) * 100,
        2
    )

    valor_corrigido = round(
        valor * fator,
        2
    )

    reajuste = round(
        valor_corrigido - valor,
        2
    )

    # ==================================================
    # RESULTADOS
    # ==================================================

    st.success("Reajuste calculado com sucesso.")

    st.metric(
        "Período utilizado",
        f"{df_filtrado.iloc[0]['mes']} até "
        f"{df_filtrado.iloc[-1]['mes']}"
    )

    st.metric(
        "IGP-M acumulado (12 meses)",
        f"{percentual:.2f}%"
    )

    st.metric(
        "Valor reajustado",
        f"R$ {valor_corrigido:,.2f}"
    )

    st.metric(
        "Valor do reajuste",
        f"R$ {reajuste:,.2f}"
    )

    # ==================================================
    # TABELA
    # ==================================================

    st.subheader("📑 Índices Utilizados")

    tabela = (
        df_filtrado[["mes", "valor"]]
        .rename(columns={
            "mes": "Mês/Ano",
            "valor": "IGP-M (%)"
        })
    )

    st.dataframe(
        tabela,
        use_container_width=True
    )

    # ==================================================
    # PDF
    # ==================================================

    pdf = gerar_pdf(
        contrato,
        contratante,
        contratada,
        objeto,
        valor,
        valor_corrigido,
        percentual,
        df_filtrado,
        responsavel
    )

    st.download_button(
        "📄 Baixar Relatório em PDF",
        data=pdf,
        file_name=(
            f"reajuste_igpm_"
            f"{datetime.now().strftime('%Y%m%d')}.pdf"
        ),
        mime="application/pdf"
    )
