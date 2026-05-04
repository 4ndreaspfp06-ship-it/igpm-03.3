import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import date

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(page_title="Relatório de Reajuste", layout="centered")

st.title("📄 Gerador de Relatório de Reajuste Contratual")

# =========================
# FORMULÁRIO
# =========================
contrato = st.text_input("Número do Contrato")
contratante = st.text_input("Contratante")
contratada = st.text_input("Contratada")
objeto = st.text_area("Objeto do Contrato")

indice = st.text_input("Índice (ex: IGP-M)")
percentual = st.text_input("Percentual (%)")
data_base = st.date_input("Data Base", value=date.today())

# =========================
# FUNÇÃO GERAR PDF
# =========================
def gerar_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    conteudo = []

    conteudo.append(Paragraph("RELATÓRIO DE REAJUSTE CONTRATUAL", styles["Title"]))
    conteudo.append(Spacer(1, 12))

    conteudo.append(Paragraph(f"<b>Contrato:</b> {contrato}", styles["Normal"]))
    conteudo.append(Paragraph(f"<b>Contratante:</b> {contratante}", styles["Normal"]))
    conteudo.append(Paragraph(f"<b>Contratada:</b> {contratada}", styles["Normal"]))
    conteudo.append(Paragraph(f"<b>Objeto:</b> {objeto}", styles["Normal"]))
    conteudo.append(Spacer(1, 12))

    conteudo.append(Paragraph("<b>Fundamentação Legal:</b>", styles["Heading2"]))
    conteudo.append(Paragraph(
        "O presente reajuste está fundamentado na Lei nº 14.133/2021, "
        "observando a manutenção do equilíbrio econômico-financeiro do contrato.",
        styles["Normal"]
    ))
    conteudo.append(Spacer(1, 12))

    conteudo.append(Paragraph("<b>Dados do Reajuste:</b>", styles["Heading2"]))
    conteudo.append(Paragraph(f"Índice: {indice}", styles["Normal"]))
    conteudo.append(Paragraph(f"Percentual aplicado: {percentual}%", styles["Normal"]))
    conteudo.append(Paragraph(f"Data base: {data_base.strftime('%d/%m/%Y')}", styles["Normal"]))
    conteudo.append(Spacer(1, 24))

    conteudo.append(Paragraph("__________________________________", styles["Normal"]))
    conteudo.append(Paragraph("Responsável", styles["Normal"]))

    doc.build(conteudo)
    buffer.seek(0)
    return buffer

# =========================
# BOTÃO GERAR PDF
# =========================
if st.button("📥 Gerar PDF"):
    if contrato and contratante and contratada:
        pdf = gerar_pdf()

        st.download_button(
            label="📄 Baixar Relatório",
            data=pdf,
            file_name="relatorio_reajuste.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Preencha os campos obrigatórios!")
