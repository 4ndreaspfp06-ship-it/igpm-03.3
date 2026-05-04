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
# BUSCAR IGP-M ONLINE
# ================================
@st.cache_data
def buscar_igpm():
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.189/dados?formato=json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except:
        return None

    df = pd.DataFrame(response.json())

    if df.empty:
        return None

    df.columns = df.columns.str.strip().str.lower()

    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = df["valor"].str.replace(",", ".").astype(float)

    df = df.dropna()
    df["mes"] = df["data"].dt.to_period("M")

    return df


df_indices = buscar_igpm()

if df_indices is None:
    st.error("Erro ao carregar IGP-M.")
    st.stop()

# ================================
# GERAR PDF PADRÃO LEI 14.133
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

    # TÍTULO
    elementos.append(Paragraph("<b>RELATÓRIO DE REAJUSTE CONTRATUAL</b>", styles["Title"]))
    elementos.append(Spacer(1, 12))

    # 1. IDENTIFICAÇÃO
    elementos.append(Paragraph("<b>1. IDENTIFICAÇÃO DO CONTRATO</b>", styles["Heading2"]))
    elementos.append(Paragraph(f"Contrato nº: {contrato}", styles["Normal"]))
    elementos.append(Paragraph(f"Contratante: {contratante}", styles["Normal"]))
    elementos.append(Paragraph(f"Contratada: {contratada}", styles["Normal"]))
    elementos.append(Paragraph(f"Objeto: {objeto}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    # 2. FUNDAMENTAÇÃO
    elementos.append(Paragraph("<b>2. FUNDAMENTAÇÃO LEGAL</b>", styles["Heading2"]))
    elementos.append(Paragraph(
        "O presente reajuste contratual está fundamentado na Lei nº 14.133/2021, "
        "que estabelece a atualização dos valores contratuais para manutenção do equilíbrio econômico-financeiro.",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    # 3. ÍNDICE
    elementos.append(Paragraph("<b>3. ÍNDICE DE REAJUSTE</b>", styles["Heading2"]))
    elementos.append(Paragraph("Índice utilizado: IGP-M (FGV)", styles["Normal"]))
    elementos.append(Paragraph(
        f"Período de aplicação: {data_inicio.strftime('%m/%Y')} até {data_fim.strftime('%m/%Y')}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    # 4. MEMÓRIA
    elementos.append(Paragraph("<b>4. MEMÓRIA DE CÁLCULO</b>", styles["Heading2"]))
    elementos.append(Paragraph(f"Valor inicial: R$ {valor:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Valor final corrigido: R$ {valor_corrigido:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Valor do reajuste: R$ {valor_reajuste:,.2f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(
        "O cálculo foi realizado com base na aplicação acumulada do índice IGP-M, "
        "considerando a variação mensal no período informado.",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    # TABELA
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

    # 5. CONCLUSÃO
    elementos.append(Paragraph("<b>5. CONCLUSÃO</b>", styles["Heading2"]))
    elementos.append(Paragraph(
        "Diante do exposto, verifica-se a necessidade de reajuste do valor contratual, "
        "a fim de garantir a manutenção do equilíbrio econômico-financeiro do contrato.",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 20))

    # ASSINATURA
    elementos.append(Paragraph(
        f"Local e data: ______________________, {datetime.now().strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph(f"Responsável pelo cálculo: {responsavel}", styles["Normal"]))
    elementos.append(Spacer(1, 30))

    elementos.append(Paragraph("Assinatura: __________________________", styles["Normal"]))

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
responsavel = st.text_input("Responsável pelo cálculo")

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
        st.warning("A data final deve ser maior que a inicial.")
        st.stop()

    mes_inicio = pd.to_datetime(data_inicio).to_period("M")
    mes_fim = pd.to_datetime(data_fim).to_period("M")

    df_filtrado = df_indices[
        (df_indices["mes"] >= mes_inicio) &
        (df_indices["mes"] <= mes_fim)
    ].copy()

    if df_filtrado.empty:
        st.error("Não há dados para o período.")
        st.stop()

    fator = (1 + df_filtrado["valor"] / 100).prod()
    valor_corrigido = valor * fator

    st.success("Reajuste calculado com sucesso!")

    st.metric("Valor corrigido", f"R$ {valor_corrigido:,.2f}")

    # GERAR PDF
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
        "📄 Baixar Relatório em PDF",
        data=pdf,
        file_name=f"reajuste_contratual_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
