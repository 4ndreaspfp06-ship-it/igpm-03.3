import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Sistema IGP-M", layout="centered")

st.title("📊 Sistema de Reajuste Contratual - IGP-M")

# 🔎 Buscar IGP-M online
def buscar_igpm():
    url = "https://www.portalbrasil.net/igpm.htm"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "lxml")
    tabela = soup.find("table")
    linhas = tabela.find_all("tr")

    dados = []

    for linha in linhas[1:]:
        colunas = linha.find_all("td")
        if len(colunas) >= 2:
            mes = colunas[0].text.strip()
            indice = colunas[1].text.strip().replace(",", ".")

            try:
                dados.append({
                    "mes": pd.to_datetime(mes, format="%m/%Y"),
                    "indice": float(indice)
                })
            except:
                continue

    return pd.DataFrame(dados)

# 📥 Carregar dados
df_indices = buscar_igpm()

# 📅 Entradas
st.subheader("📅 Período")
data_inicio = st.date_input("Data inicial")
data_fim = st.date_input("Data final")

st.subheader("💰 Dados do Contrato")
valor_inicial = st.number_input("Valor inicial (R$)", format="%.2f")

numero_contrato = st.text_input("Número do contrato")
contratante = st.text_input("Contratante")
contratada = st.text_input("Contratada")
objeto = st.text_input("Objeto do contrato")

# 🚀 Calcular
if st.button("Calcular"):

    if data_fim <= data_inicio:
        st.error("Data final deve ser maior que a inicial")
    else:

        df_filtrado = df_indices[
            (df_indices["mes"] >= pd.to_datetime(data_inicio)) &
            (df_indices["mes"] <= pd.to_datetime(data_fim))
        ].sort_values("mes")

        valor = valor_inicial
        tabela = []
        valores = []
        meses = []

        for _, row in df_filtrado.iterrows():
            indice = row["indice"]
            reajuste = valor * (indice / 100)
            valor_final = valor + reajuste

            tabela.append({
                "Mês": row["mes"].strftime("%m/%Y"),
                "Índice (%)": f"{indice:.2f}",
                "Valor Inicial (R$)": f"{valor:.2f}",
                "Reajuste (R$)": f"{reajuste:.2f}",
                "Valor Final (R$)": f"{valor_final:.2f}"
            })

            valores.append(valor_final)
            meses.append(row["mes"].strftime("%m/%Y"))

            valor = valor_final

        df_resultado = pd.DataFrame(tabela)

        # 📋 Tabela
        st.subheader("📋 Tabela Mês a Mês")
        st.dataframe(df_resultado, use_container_width=True)

        # 📊 Gráfico
        st.subheader("📊 Evolução")
        fig, ax = plt.subplots()
        ax.plot(meses, valores)
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # 📊 Resumo
        reajuste_total = valor - valor_inicial

        st.subheader("📊 Resumo")
        st.write(f"Valor inicial: R$ {valor_inicial:.2f}")
        st.write(f"Valor final: R$ {valor:.2f}")
        st.write(f"Reajuste total: R$ {reajuste_total:.2f}")

        # 📁 Exportar Excel
        caminho_excel = "resultado.xlsx"
        df_resultado.to_excel(caminho_excel, index=False)

        with open(caminho_excel, "rb") as f:
            st.download_button("📥 Baixar Excel", f, "resultado.xlsx")

        # 📄 Gerar PDF padrão Lei 14.133
        if st.button("Gerar PDF"):

            doc = SimpleDocTemplate("relatorio.pdf")
            styles = getSampleStyleSheet()

            texto = f"""
RELATÓRIO DE REAJUSTE CONTRATUAL

1. IDENTIFICAÇÃO DO CONTRATO
Contrato nº: {numero_contrato}
Contratante: {contratante}
Contratada: {contratada}
Objeto: {objeto}

2. FUNDAMENTAÇÃO LEGAL
Lei nº 14.133/2021 – manutenção do equilíbrio econômico-financeiro.

3. ÍNDICE DE REAJUSTE
IGP-M (FGV)
Período: {data_inicio} até {data_fim}

4. MEMÓRIA DE CÁLCULO
Valor inicial: R$ {valor_inicial:.2f}
Valor final: R$ {valor:.2f}
Reajuste: R$ {reajuste_total:.2f}

5. CONCLUSÃO
Verifica-se a necessidade de reajuste para manutenção do equilíbrio contratual.
"""

            elementos = []
            for linha in texto.split("\n"):
                elementos.append(Paragraph(linha, styles["Normal"]))
                elementos.append(Spacer(1, 8))

            doc.build(elementos)

            with open("relatorio.pdf", "rb") as f:
                st.download_button("📄 Baixar PDF", f, "relatorio.pdf")
