import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import time
# Gerar PDF
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
# ---- #
st.set_page_config(page_title="Análise de Ações", layout="wide")

# --- TRUQUE VISUAL: FORÇAR MAIÚSCULAS APENAS NO TICKER ---
st.markdown(
    """
    <style>
    input[aria-label="Ticker da ação (ex: AAPL, MSFT, NVDA, AMD)"] {
        text-transform: uppercase;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ✅ Função para gerar o PDF
def gerar_pdf(ticker, info, dados_formulario, figuras):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle('Titulo', parent=styles['Title'], fontSize=18, spaceAfter=6)
    estilo_h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=14, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor('#1f77b4'))
    estilo_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=11, spaceBefore=8, spaceAfter=4)
    estilo_normal = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=9, spaceAfter=4)
    estilo_label = ParagraphStyle('Label', parent=styles['Normal'], fontSize=8, textColor=colors.grey)

    story = []

    nome = info.get("longName", ticker.upper())
    story.append(Paragraph(f"Análise de Ações: {nome} ({ticker.upper()})", estilo_titulo))
    story.append(Paragraph(f"Setor: {info.get('sector','N/D')} | Indústria: {info.get('industry','N/D')} | País: {info.get('country','N/D')}", estilo_normal))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceAfter=10))

    def campo(label, valor):
        if valor and str(valor).strip() and str(valor).strip() not in ["Preencher", ""]:
            story.append(Paragraph(f"<b>{label}:</b> {valor}", estilo_normal))

    story.append(Paragraph("1. Macro e Setorial", estilo_h1))
    campo("Tendência do índice", dados_formulario.get("tendencia"))
    campo("Sentimento Mundial", dados_formulario.get("sentimento"))
    campo("Situação do País", dados_formulario.get("sit_pais"))
    campo("Estabilidade", dados_formulario.get("estabilidade"))
    campo("PIB e Emprego", dados_formulario.get("pib_emprego"))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=6))

    story.append(Paragraph("2. Negócio / Empresa", estilo_h1))
    descricao = info.get("longBusinessSummary", "")
    if descricao:
        story.append(Paragraph(descricao[:600] + "..." if len(descricao) > 600 else descricao, estilo_normal))
        story.append(Spacer(1, 6))
    campo("O que vende", dados_formulario.get("o_que_vende"))
    campo("Onde opera", dados_formulario.get("onde_opera"))
    campo("Como ganha dinheiro", dados_formulario.get("como_ganha"))
    campo("Líder de mercado", dados_formulario.get("lider"))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=6))

    story.append(Paragraph("3. Qualitativa e Risco", estilo_h1))
    campo("MOAT", dados_formulario.get("moat"))
    campo("Descrição do MOAT", dados_formulario.get("moat_desc"))
    campo("Liderança", dados_formulario.get("lideranca"))
    campo("Visão Estratégica", dados_formulario.get("visao"))
    campo("Ações (Buybacks)", dados_formulario.get("acoes_empresa"))
    campo("Riscos", dados_formulario.get("riscos"))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=6))

    story.append(Paragraph("4. Quantitativa", estilo_h1))
    story.append(Paragraph("4.1 Evolução: Financeira e Acionária", estilo_h2))

    # ✅ ALTERADO: substituído fig.to_image (kaleido) por notas de texto
    nomes_graficos = ["Receita vs Lucro Líquido", "CFO vs FCF", "EBITDA", "Ações em Circulação"]
    chaves_notas = ["notas_receita", "notas_cf", "notas_ebitda", "notas_shares"]
    estilo_grafico = ParagraphStyle('Grafico', parent=styles['Normal'], fontSize=9,
                                    textColor=colors.HexColor('#1f77b4'),
                                    borderColor=colors.HexColor('#1f77b4'),
                                    borderWidth=1, borderPadding=8,
                                    spaceAfter=4)
    for i, fig in enumerate(figuras):
        if fig is not None:
            story.append(Paragraph(f"📊 Gráfico disponível na app: <b>{nomes_graficos[i]}</b>", estilo_grafico))
        nota = dados_formulario.get(chaves_notas[i], "")
        if nota and nota.strip():
            story.append(Paragraph(f"<i>Notas: {nota}</i>", estilo_label))
        story.append(Spacer(1, 8))

    story.append(Paragraph("4.2 Métricas de Crescimento e Eficiência", estilo_h2))
    cres_rec = info.get("revenueGrowth", None)
    cres_luc = info.get("earningsGrowth", None)
    dados_metricas = [
        ["Métrica", "Valor"],
        ["Crescimento Receita (YoY)", f"{cres_rec*100:.1f}%" if cres_rec else "N/D"],
        ["Crescimento Lucro (YoY)", f"{cres_luc*100:.1f}%" if cres_luc else "N/D"],
        ["CCC", dados_formulario.get("ccc", "N/D")],
    ]
    t = Table(dados_metricas, colWidths=[9*cm, 7*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.3 Performance", estilo_h2))
    mg = info.get("grossMargins", None)
    mo_v = info.get("operatingMargins", None)
    mn = info.get("profitMargins", None)
    roe = info.get("returnOnEquity", None)
    dados_perf = [
        ["Métrica", "Valor"],
        ["Margem Bruta (TTM)", f"{mg*100:.1f}%" if mg else "N/D"],
        ["Margem Operacional (TTM)", f"{mo_v*100:.1f}%" if mo_v else "N/D"],
        ["Margem Líquida (TTM)", f"{mn*100:.1f}%" if mn else "N/D"],
        ["ROE (TTM)", f"{roe*100:.1f}%" if roe else "N/D"],
        ["ROIC", dados_formulario.get("roic", "N/D")],
    ]
    t2 = Table(dados_perf, colWidths=[9*cm, 7*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(t2)
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.4 Saúde Financeira & Valuation", estilo_h2))
    divida = info.get("totalDebt", None)
    ebitda_v = info.get("ebitda", None)
    cr = info.get("currentRatio", None)
    de = info.get("debtToEquity", None)
    div_yield = info.get("dividendYield", None)
    payout = info.get("payoutRatio", None)
    pe = info.get("trailingPE", None)
    ps = info.get("priceToSalesTrailing12Months", None)
    pb = info.get("priceToBook", None)
    ev_ebitda = info.get("enterpriseToEbitda", None)
    dados_saude = [
        ["Métrica", "Valor"],
        ["DEBT/EBITDA", f"{divida/ebitda_v:.1f}x" if divida and ebitda_v else "N/D"],
        ["Current Ratio", f"{cr:.2f}" if cr else "N/D"],
        ["DEBT/EQUITY", f"{de:.1f}" if de else "N/D"],
        ["Dívida Total", f"${divida/1e9:.1f}B" if divida else "N/D"],
        ["Dividend Yield", f"{div_yield*100:.2f}%" if div_yield else "N/D"],
        ["Payout Ratio", f"{payout*100:.1f}%" if payout else "N/D"],
        ["P/E Ratio", f"{pe:.1f}" if pe else "N/D"],
        ["P/S Ratio", f"{ps:.1f}" if ps else "N/D"],
        ["P/B Ratio", f"{pb:.1f}" if pb else "N/D"],
        ["EV/EBITDA", f"{ev_ebitda:.1f}" if ev_ebitda else "N/D"],
    ]
    t3 = Table(dados_saude, colWidths=[9*cm, 7*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(t3)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=6))

    story.append(Paragraph("5. Valor Intrínseco", estilo_h1))
    preco_atual = info.get("currentPrice", None)
    eps = info.get("trailingEps", None)
    peg = info.get("pegRatio", None)
    campo("Preço Atual", f"${preco_atual:.2f}" if preco_atual else "N/D")
    campo("EPS", f"${eps:.2f}" if eps else "N/D")
    campo("PEG Ratio", f"{peg:.2f}" if peg else "N/D")
    campo("Valor Intrínseco Estimado", f"${dados_formulario.get('valor_intriseco', 0):.2f}")
    campo("Margem de Segurança", dados_formulario.get("margem_seguranca", "N/D"))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=6))

    story.append(Paragraph("6. Conclusão Final", estilo_h1))
    campo("Data da análise", str(dados_formulario.get("data_analise", "")))
    campo("Motivo de compra", dados_formulario.get("motivo_compra"))
    campo("Período", dados_formulario.get("periodo"))
    campo("Critérios a manter", dados_formulario.get("criterios"))
    campo("Quando vender", dados_formulario.get("quando_vendo"))
    decisao_val = dados_formulario.get("decisao", "")
    cor_decisao = colors.green if "Comprar" in decisao_val else (colors.orange if "Aguardar" in decisao_val else colors.red)
    estilo_decisao = ParagraphStyle('Decisao', parent=styles['Normal'], fontSize=12, textColor=cor_decisao, spaceBefore=8)
    story.append(Paragraph(f"<b>Decisão Final: {decisao_val}</b>", estilo_decisao))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ✅ Função do botão de download
def botao_pdf():
    figuras = [
        st.session_state.get('fig_receita_lucro'),  # ✅ ALTERADO
        st.session_state.get('fig_cfo_fcf'),         # ✅ ALTERADO
        st.session_state.get('fig_ebitda'),
        st.session_state.get('fig_shares'),
    ]
    dados = {
        "tendencia": st.session_state.get("tendencia", ""),
        "sentimento": st.session_state.get("sentimento", ""),
        "sit_pais": st.session_state.get("sit_pais", ""),
        "estabilidade": st.session_state.get("estabilidade", ""),
        "pib_emprego": st.session_state.get("pib_emprego", ""),
        "o_que_vende": st.session_state.get("o_que_vende", ""),
        "onde_opera": st.session_state.get("onde_opera", ""),
        "como_ganha": st.session_state.get("como_ganha", ""),
        "lider": st.session_state.get("lider", ""),
        "moat": st.session_state.get("moat", ""),
        "moat_desc": st.session_state.get("moat_desc", ""),
        "lideranca": st.session_state.get("lideranca", ""),
        "visao": st.session_state.get("visao", ""),
        "acoes_empresa": st.session_state.get("acoes_empresa", ""),
        "riscos": st.session_state.get("riscos", ""),
        "notas_receita": st.session_state.get("notas_receita", ""),
        "notas_cf": st.session_state.get("notas_cf", ""),
        "notas_ebitda": st.session_state.get("notas_ebitda", ""),
        "notas_shares": st.session_state.get("notas_shares", ""),
        "ccc": st.session_state.get("ccc_valor", "N/D"),
        "roic": st.session_state.get("roic_valor", "N/D"),
        "valor_intriseco": st.session_state.get("valor_intriseco", 0),
        "margem_seguranca": st.session_state.get("margem_seguranca", "N/D"),
        "data_analise": st.session_state.get("data_analise", ""),
        "motivo_compra": st.session_state.get("motivo_compra", ""),
        "periodo": st.session_state.get("periodo", ""),
        "criterios": st.session_state.get("criterios", ""),
        "quando_vendo": st.session_state.get("quando_vendo", ""),
        "decisao": st.session_state.get("decisao", ""),
    }
    pdf_buffer = gerar_pdf(ticker, info, dados, figuras)
    st.download_button(
        label="📄 Exportar Análise para PDF",
        data=pdf_buffer,
        file_name=f"analise_{ticker.upper()}.pdf",
        mime="application/pdf",
        use_container_width=True,
        key=f"pdf_btn_{id(dados)}"
    )

# --- TRUQUE DE MESTRE: CACHE ---
@st.cache_data(ttl=3600)
def obter_dados_alpha_vantage(ticker_symbol, api_key):
    url_is = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker_symbol}&apikey={api_key}"
    res_is = requests.get(url_is).json()
    time.sleep(2) # Pausa obrigatória de 2 segundos
    url_cf = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker_symbol}&apikey={api_key}"
    res_cf = requests.get(url_cf).json()
    return res_is, res_cf

# --- BARRA LATERAL PARA A API KEY ---
st.sidebar.header("Configurações")
av_api_key = st.sidebar.text_input("API Key do Alpha Vantage", type="password", help="Obtém a tua chave gratuita em alphavantage.co")
st.sidebar.markdown("*(Limite da versão gratuita: 25 pesquisas por dia)*")
if st.sidebar.button("Limpar Memória (Cache)"):
    st.cache_data.clear()
    st.sidebar.success("Memória limpa!")

st.title("Análise de Ações")

ticker = st.text_input("Ticker da ação (ex: AAPL, MSFT, NVDA, AMD)")

if ticker:
    with st.spinner('A processar dados...'):
        acao = yf.Ticker(ticker)
        info = acao.info

        # Puxar tabelas do yfinance para os cálculos manuais
        bs = acao.balance_sheet
        fin = acao.financials

        nome = info.get("longName", "N/D")
        st.subheader(f"{nome} ({ticker.upper()})")
        st.caption(f"Setor: {info.get('sector', 'N/D')} | Indústria: {info.get('industry', 'N/D')} | País: {info.get('country', 'N/D')}")

        # ✅ Botão PDF no topo
        botao_pdf()

        st.divider()

        # ── 1. MACRO E SETORIAL ──────────────────────────────────────────────
        st.header("1. Macro e Setorial")

        # Criamos 5 colunas para manter tudo na mesma linha
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.write("Tendência do índice")
            tendencia = st.selectbox("Qual a tendência do mercado/índice?", ["Preencher", "Bull", "Bear", "Lateral"], key="tendencia")
        with col2:
            st.write("Sentimento Mundial")
            sentimento = st.selectbox("Qual é a saúde económica global?", ["Preencher", "Bull", "Bear", "Lateral"], key="sentimento")
        with col3:
            st.write("País")
            sit_pais = st.selectbox("Situação económica do país/região?", ["Preencher", "Expansão", "Pico/ Auge", "Recessão", "Recuperação"], key="sit_pais")
        with col4:
            st.markdown("&nbsp;")
            estabilidade = st.selectbox("É estável, transparente e estimulada?", ["Preencher", "Sim", "Não"], key="estabilidade")
        with col5:
            st.markdown("&nbsp;")
            pib_emprego = st.selectbox("PIB e mercado de trabalho?", ["Preencher", "Bom", "Moderado", "Mau"], key="pib_emprego")

        st.divider()

        # ── 2. NEGÓCIO / EMPRESA ─────────────────────────────────────────────
        st.header("2. Negócio / Empresa")

        descricao = info.get("longBusinessSummary", "")
        if descricao:
            with st.expander("Descrição do negócio (fonte: Yahoo Finance)"):
                st.write(descricao)

        col1, col2 = st.columns(2)
        with col1:
            o_que_vende = st.text_area("O que vende?", placeholder="Explicar numa frase curta", key="o_que_vende")
            onde_opera = st.text_input("Onde opera?", placeholder="Explicar numa frase curta", key="onde_opera")
        with col2:
            como_ganha = st.text_area("Como ganha dinheiro?", placeholder="Explicar numa frase curta", key="como_ganha")
            lider = st.selectbox("É líder de mercado?", ["Preencher", "Sim", "Não"], key="lider")
            if lider == "Sim":
                qual_lider = st.text_input("Qual?", placeholder="Indicar qual o mercado", key="qual_lider")
            elif lider == "Não":
                quem_lider = st.text_input("Qual é?", placeholder="Indicar o ticker da concorrente", key="quem_lider")

        st.divider()

        # ── 3. QUALITATIVA E RISCO ───────────────────────────────────────────
        st.header("3. Qualitativa e Risco")

        col1, col2 = st.columns(2)
        with col1:
            # Corrigido o erro do parêntesis a mais
            moat = st.selectbox("Tem MOAT?", ["Preencher", "Sim", "Não"], key="moat")
            if moat == "Sim":
                moat_desc = st.text_area("Descreve o MOAT:", placeholder="Tem uma marca forte?...", key="moat_desc")
            lideranca = st.text_area("Liderança (CEO, diretores):", key="lideranca")
        with col2:
            visao = st.text_area("Visão estratégica da gestão:", key="visao")
            acoes_empresa = st.selectbox("Ações da empresa (buybacks?)", ["Sim - reduz ações", "Não", "Dilui acionistas"], key="acoes_empresa")
            riscos = st.text_area("Riscos identificados:", key="riscos")

        st.divider()

        # ── 4. QUANTITATIVA ──────────────────────────────────────────────────
        st.header("4. Quantitativa")

        # 4.1 Evolução Histórica
        st.subheader("4.1 Evolução: Financeira e Acionária")

        col_g1, col_g2 = st.columns(2)
        col_g3, col_g4 = st.columns(2)

        df_is = None # Inicializamos para usar na Secção das Margens mais à frente

        if av_api_key:
            try:
                is_data, cf_data = obter_dados_alpha_vantage(ticker, av_api_key)

                if "annualReports" in is_data and "annualReports" in cf_data:
                    df_is = pd.DataFrame(is_data["annualReports"][:5])
                    df_cf = pd.DataFrame(cf_data["annualReports"][:5])

                    df_is['fiscalDateEnding'] = pd.to_datetime(df_is['fiscalDateEnding']).dt.year.astype(str)
                    df_is = df_is.iloc[::-1].reset_index(drop=True)

                    df_cf['fiscalDateEnding'] = pd.to_datetime(df_cf['fiscalDateEnding']).dt.year.astype(str)
                    df_cf = df_cf.iloc[::-1].reset_index(drop=True)

                    anos_fin = df_is['fiscalDateEnding']
                    anos_cf = df_cf['fiscalDateEnding']

                    rev_hist = pd.to_numeric(df_is['totalRevenue'], errors='coerce').fillna(0) / 1e9
                    net_hist = pd.to_numeric(df_is['netIncome'], errors='coerce').fillna(0) / 1e9
                    ebitda_hist = pd.to_numeric(df_is['ebitda'], errors='coerce').fillna(0) / 1e9

                    cfo_hist = pd.to_numeric(df_cf['operatingCashflow'], errors='coerce').fillna(0) / 1e9
                    capex_hist = pd.to_numeric(df_cf['capitalExpenditures'], errors='coerce').fillna(0) / 1e9
                    fcf_hist = cfo_hist - capex_hist

                    ttm_rev = info.get("totalRevenue", 0) / 1e9
                    ttm_net = info.get("netIncomeToCommon", 0) / 1e9
                    ttm_ebitda = info.get("ebitda", 0) / 1e9
                    ttm_cfo = info.get("operatingCashflow", 0) / 1e9
                    ttm_fcf = info.get("freeCashflow", 0) / 1e9

                    with col_g1:
                        # ✅ ALTERADO: nome da variável corrigido para fig_res_luc em todas as linhas
                        fig_res_luc = go.Figure()
                        fig_res_luc.add_trace(go.Bar(x=anos_fin, y=rev_hist, name='Receita', marker_color='#1f77b4', text=rev_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_res_luc.add_trace(go.Bar(x=anos_fin, y=net_hist, name='Lucro Líquido', marker_color='#FFD700', text=net_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_res_luc.add_trace(go.Bar(x=['TTM'], y=[ttm_rev], name='Receita (TTM)', marker_color='#1f77b4', opacity=0.6, showlegend=False, text=[f"{ttm_rev:.1f}"], textposition='auto', textfont=dict(color='white')))
                        fig_res_luc.add_trace(go.Bar(x=['TTM'], y=[ttm_net], name='Lucro (TTM)', marker_color='#FFD700', opacity=0.6, showlegend=False, text=[f"{ttm_net:.1f}"], textposition='auto', textfont=dict(color='white')))
                        fig_res_luc.update_layout(title="Receita vs Lucro Líquido", barmode='group', template='plotly_dark', height=400, margin=dict(t=50, b=20), yaxis_title="Biliões de USD ($B)", yaxis_title_font_size=16, bargap=0.1)
                        st.plotly_chart(fig_res_luc, use_container_width=True)
                        st.session_state['fig_receita_lucro'] = fig_res_luc
                        st.text_area("📝 Notas — Receita vs Lucro", placeholder="Observações sobre receita e lucro líquido...", height=100, key="notas_receita")

                    with col_g2:
                        # ✅ ALTERADO: nome da variável corrigido para fig_cfo_fcf em todas as linhas
                        fig_cfo_fcf = go.Figure()
                        fig_cfo_fcf.add_trace(go.Bar(x=anos_cf, y=cfo_hist, name='CFO', marker_color='#FF9F1C', text=cfo_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_cfo_fcf.add_trace(go.Bar(x=anos_cf, y=fcf_hist, name='FCF', marker_color='#2EC4B6', text=fcf_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_cfo_fcf.add_trace(go.Bar(x=['TTM'], y=[ttm_cfo], name='CFO (TTM)', marker_color='#FF9F1C', opacity=0.6, showlegend=False, text=[f"{ttm_cfo:.1f}"], textposition='auto', textfont=dict(color='white')))
                        fig_cfo_fcf.add_trace(go.Bar(x=['TTM'], y=[ttm_fcf], name='FCF (TTM)', marker_color='#2EC4B6', opacity=0.6, showlegend=False, text=[f"{ttm_fcf:.1f}"], textposition='auto', textfont=dict(color='white')))
                        fig_cfo_fcf.update_layout(title="Cash From Operations (CFO) vs Free Cash Flow (FCF)", barmode='group', template='plotly_dark', height=400, margin=dict(t=50, b=20), yaxis_title="Biliões de USD ($B)", yaxis_title_font_size=16, bargap=0.1)
                        st.plotly_chart(fig_cfo_fcf, use_container_width=True)
                        st.session_state['fig_cfo_fcf'] = fig_cfo_fcf
                        st.text_area("📝 Notas — CFO vs FCF", placeholder="Observações sobre cash flow operacional e free cash flow...", height=100, key="notas_cf")

                    with col_g3:
                        fig_ebitda = go.Figure()
                        fig_ebitda.add_trace(go.Bar(x=anos_fin, y=ebitda_hist, name='EBITDA', marker_color='#00CC96', text=ebitda_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_ebitda.add_trace(go.Bar(x=['TTM'], y=[ttm_ebitda], name='EBITDA (TTM)', marker_color='#00CC96', opacity=0.6, showlegend=False, text=[f"{ttm_ebitda:.1f}"], textposition='auto', textfont=dict(color='white')))
                        fig_ebitda.update_layout(title="EBITDA", template='plotly_dark', height=280, margin=dict(t=50, b=20), yaxis_title="Biliões de USD ($B)", yaxis_title_font_size=16, bargap=0.6)
                        st.plotly_chart(fig_ebitda, use_container_width=True)
                        st.session_state['fig_ebitda'] = fig_ebitda
                        st.text_area("📝 Notas — EBITDA", placeholder="Observações sobre o EBITDA...", height=100, key="notas_ebitda")

                else:
                    if "annualReports" not in is_data:
                        st.warning(f"O Alpha Vantage bloqueou o pedido de Receitas: {is_data.get('Information', is_data.get('Note', is_data))}")
                    elif "annualReports" not in cf_data:
                        st.warning(f"O Alpha Vantage bloqueou o pedido de Cash Flow: {cf_data.get('Information', cf_data.get('Note', cf_data))}")

            except Exception as e:
                st.error(f"Erro ao processar dados da API Alpha Vantage: {e}")
        else:
            st.info("👈 Por favor, insere a tua API Key do Alpha Vantage na barra lateral para carregar os gráficos históricos.")

        # Gráfico das Ações em Circulação
        with col_g4:
            try:
                if 'Ordinary Shares Number' in bs.index:
                    shares_series = bs.loc['Ordinary Shares Number'].dropna().sort_index(ascending=True)
                    anos_shares = shares_series.index.year.astype(str)
                    val_shares = shares_series.values / 1e6 # Milhões

                    min_y = min(val_shares) * 0.98 if len(val_shares) > 0 else 0
                    max_y = max(val_shares) * 1.02 if len(val_shares) > 0 else 100

                    fig_shares = go.Figure()
                    fig_shares.add_trace(go.Bar(
                        x=anos_shares, y=val_shares, marker_color='#8E44AD', name='Shares',
                        text=[f"{v:.0f}" for v in val_shares], textposition='auto', textfont=dict(color='white')
                    ))
                    fig_shares.update_layout(
                        title="Ordinary Shares Number", template='plotly_dark', height=280, margin=dict(t=50, b=20),
                        yaxis_title="Milhões (M)", yaxis_title_font_size=16, bargap=0.6
                    )
                    fig_shares.update_yaxes(range=[min_y, max_y])
                    st.plotly_chart(fig_shares, use_container_width=True)
                    st.session_state['fig_shares'] = fig_shares
                    st.text_area("📝 Notas — Ações em Circulação", placeholder="Observações sobre buybacks ou diluição...", height=100, key="notas_shares")
                else:
                    st.info("Não foi possível encontrar o histórico de 'Ordinary Shares Number' para esta empresa.")
            except Exception as e:
                st.warning(f"Erro ao desenhar o gráfico de ações: {e}")

        st.divider()

        # 4.2 Métricas Atuais de Crescimento e CCC
        st.subheader("4.2 Métricas Atuais de Crescimento e Eficiência")

        col1, col2, col3 = st.columns(3)

        crescimento_receita = info.get("revenueGrowth", None)
        col1.metric("Crescimento Receita (YoY)", f"{crescimento_receita*100:.1f}%" if crescimento_receita else "N/D")

        crescimento_lucro = info.get("earningsGrowth", None)
        col2.metric("Crescimento Lucro (YoY)", f"{crescimento_lucro*100:.1f}%" if crescimento_lucro else "N/D")

        # CÁLCULO MANUAL DO CCC
        try:
            inventory = bs.loc['Inventory'].iloc[0] if 'Inventory' in bs.index else 0
            cogs = abs(fin.loc['Cost Of Revenue'].iloc[0]) if 'Cost Of Revenue' in fin.index else 0
            receivables = bs.loc['Accounts Receivable'].iloc[0] if 'Accounts Receivable' in bs.index else (bs.loc['Receivables'].iloc[0] if 'Receivables' in bs.index else 0)
            revenue = fin.loc['Total Revenue'].iloc[0]
            payables = bs.loc['Accounts Payable'].iloc[0] if 'Accounts Payable' in bs.index else 0

            if cogs > 0 and revenue > 0:
                dio = (inventory / cogs) * 365
                dso = (receivables / revenue) * 365
                dpo = (payables / cogs) * 365
                ccc = dio + dso - dpo
                col3.metric("Cash Conv. Cycle (CCC)", f"{int(ccc)} dias")
                st.session_state['ccc_valor'] = f"{int(ccc)} dias"
            else:
                col3.metric("Cash Conv. Cycle (CCC)", "N/D")
        except:
            col3.metric("Cash Conv. Cycle (CCC)", "N/D")

        # 4.3 Performance
        st.subheader("4.3 Métricas de Performance")
        col1, col2, col3, col4, col5 = st.columns(5)

        mg = info.get("grossMargins", None)
        col1.metric("Margem Bruta Atual (TTM)", f"{mg*100:.1f}%" if mg else "N/D")

        mo = info.get("operatingMargins", None)
        col2.metric("Margem Operacional Atual (TTM)", f"{mo*100:.1f}%" if mo else "N/D")

        mn = info.get("profitMargins", None)
        col3.metric("Margem Líquida Atual (TTM)", f"{mn*100:.1f}%" if mn else "N/D")

        roe = info.get("returnOnEquity", None)
        col4.metric("ROE (TTM)", f"{roe*100:.1f}%" if roe else "N/D")

        # CÁLCULO MANUAL DO ROIC
        try:
            ebit = fin.loc['EBIT'].iloc[0]
            tax_provision = fin.loc['Tax Provision'].iloc[0] if 'Tax Provision' in fin.index else 0
            pretax_income = fin.loc['Pretax Income'].iloc[0] if 'Pretax Income' in fin.index else ebit
            tax_rate = tax_provision / pretax_income if pretax_income > 0 else 0.21
            nopat = ebit * (1 - tax_rate)
            total_assets = bs.loc['Total Assets'].iloc[0]
            current_liab = bs.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in bs.index else 0
            invested_capital = total_assets - current_liab
            roic_val = (nopat / invested_capital) * 100
            col5.metric("ROIC", f"{roic_val:.1f}%")
            st.session_state['roic_valor'] = f"{roic_val:.1f}%"
        except:
            col5.metric("ROIC", "N/D")

        # --- GRÁFICO DAS MARGENS ---
        try:
            if df_is is not None and not df_is.empty:
                rev_m = pd.to_numeric(df_is['totalRevenue'], errors='coerce').replace(0, pd.NA)
                gp_m = pd.to_numeric(df_is['grossProfit'], errors='coerce')
                op_m = pd.to_numeric(df_is['operatingIncome'], errors='coerce')
                ni_m = pd.to_numeric(df_is['netIncome'], errors='coerce')

                mb_hist = (gp_m / rev_m * 100).fillna(0)
                mo_hist = (op_m / rev_m * 100).fillna(0)
                ml_hist = (ni_m / rev_m * 100).fillna(0)

                anos_margins = df_is['fiscalDateEnding']

                fig_margins = go.Figure()
                fig_margins.add_trace(go.Bar(x=anos_margins, y=mb_hist, name='Margem Bruta', marker_color='#3498db', text=mb_hist.apply(lambda x: f"{x:.1f}%"), textposition='auto', textfont=dict(color='white')))
                fig_margins.add_trace(go.Bar(x=anos_margins, y=mo_hist, name='Margem Operacional', marker_color='#e67e22', text=mo_hist.apply(lambda x: f"{x:.1f}%"), textposition='auto', textfont=dict(color='white')))
                fig_margins.add_trace(go.Bar(x=anos_margins, y=ml_hist, name='Margem Líquida', marker_color='#2ecc71', text=ml_hist.apply(lambda x: f"{x:.1f}%"), textposition='auto', textfont=dict(color='white')))
                fig_margins.update_layout(
                    title="Evolução Histórica das Margens (Alpha Vantage)",
                    barmode='group', template='plotly_dark', height=400, margin=dict(t=50, b=20),
                    yaxis_title="Percentagem (%)", yaxis_title_font_size=16
                )
                st.plotly_chart(fig_margins, use_container_width=True)
            else:
                st.info("Para ver a Evolução Histórica das Margens, insere a API Key do Alpha Vantage na barra lateral.")
        except Exception as e:
            st.warning(f"Erro ao processar gráfico de margens históricas: {e}")

        st.divider()

        # 4.4 Saúde Financeira
        st.subheader("4.4 Saúde Financeira")
        col1, col2, col3, col4 = st.columns(4)

        divida = info.get("totalDebt", None)
        ebitda_val = info.get("ebitda", None)
        if divida and ebitda_val and ebitda_val != 0:
            debt_ebitda = divida / ebitda_val
            col1.metric("DEBT / EBITDA", f"{debt_ebitda:.1f}x")
        else:
            col1.metric("DEBT / EBITDA", "N/D")

        # CÁLCULO MANUAL DO INTEREST COVERAGE RATIO
        try:
            ebit_val = fin.loc['EBIT'].iloc[0]
            interest_exp = abs(fin.loc['Interest Expense'].iloc[0]) if 'Interest Expense' in fin.index else 0
            if interest_exp > 0:
                icr_val = ebit_val / interest_exp
                col2.metric("Interest Coverage Ratio", f"{icr_val:.1f}x")
            else:
                col2.metric("Interest Coverage Ratio", "Seguro (S/ Despesa)")
        except:
            col2.metric("Interest Coverage Ratio", "N/D")

        cr = info.get("currentRatio", None)
        col3.metric("Current Ratio", f"{cr:.2f}" if cr else "N/D")

        fcf = info.get("freeCashflow", None)
        if divida and fcf and fcf != 0:
            debt_fcf = divida / fcf
            col4.metric("Total DEBT / FCF", f"{debt_fcf:.1f}x")
        else:
            col4.metric("Total DEBT / FCF", "N/D")

        # 4.5 Alavancagem
        st.subheader("4.5 Alavancagem Financeira")
        col1, col2 = st.columns(2)

        de = info.get("debtToEquity", None)
        col1.metric("DEBT / EQUITY", f"{de:.1f}" if de else "N/D")
        col2.metric("Dívida Total", f"${divida/1e9:.1f}B" if divida else "N/D")

        # 4.6 Dividendos
        st.subheader("4.6 Dividendos")
        col1, col2, col3 = st.columns(3)

        div_yield = info.get("dividendYield", None)
        col1.metric("Dividend Yield", f"{div_yield*100:.2f}%" if div_yield else "N/D")

        payout = info.get("payoutRatio", None)
        col2.metric("Payout Ratio", f"{payout*100:.1f}%" if payout else "N/D")

        shares = info.get("sharesOutstanding", None)
        col3.metric("Ações em Circulação Atual", f"{shares/1e9:.2f}B" if shares else "N/D")

        # 4.7 Valuation
        st.subheader("4.7 Valuation")
        col1, col2, col3, col4 = st.columns(4)

        pe = info.get("trailingPE", None)
        col1.metric("P/E Ratio", f"{pe:.1f}" if pe else "N/D")

        ps = info.get("priceToSalesTrailing12Months", None)
        col2.metric("P/S Ratio", f"{ps:.1f}" if ps else "N/D")

        pb = info.get("priceToBook", None)
        col3.metric("P/B Ratio", f"{pb:.1f}" if pb else "N/D")

        ev_ebitda = info.get("enterpriseToEbitda", None)
        col4.metric("EV/EBITDA", f"{ev_ebitda:.1f}" if ev_ebitda else "N/D")

        st.divider()

        # ── 5. VALOR INTRÍNSECO ──────────────────────────────────────────────
        st.header("5. Valor Intrínseco")
        col1, col2, col3 = st.columns(3)

        preco_atual = info.get("currentPrice", None)
        col1.metric("Preço Atual", f"${preco_atual:.2f}" if preco_atual else "N/D")

        eps = info.get("trailingEps", None)
        col2.metric("EPS (normalizado)", f"${eps:.2f}" if eps else "N/D")

        peg = info.get("pegRatio", None)
        col3.metric("PEG Ratio", f"{peg:.2f}" if peg else "N/D")

        col1, col2 = st.columns(2)
        with col1:
            valor_intriseco = st.number_input("Valor Intrínseco Estimado ($)", min_value=0.0, step=0.5, key="valor_intriseco")
        with col2:
            if valor_intriseco > 0 and preco_atual:
                margem = ((valor_intriseco - preco_atual) / valor_intriseco) * 100
                col2.metric("Margem de Segurança", f"{margem:.1f}%",
                            delta="Subvalorizada" if margem > 0 else "Sobrevalorizada")
                st.session_state['margem_seguranca'] = f"{margem:.1f}%"

        st.divider()

        # ── 6. CONCLUSÃO FINAL ───────────────────────────────────────────────
        st.header("6. Conclusão Final")

        col1, col2 = st.columns(2)
        with col1:
            data_analise = st.date_input("Data da análise", key="data_analise")
            motivo_compra = st.text_area("Motivo principal da compra:", key="motivo_compra")
            periodo = st.selectbox("Período de investimento", ["Curto prazo (<1 ano)", "Médio prazo (1-3 anos)", "Longo prazo (>3 anos)"], key="periodo")
        with col2:
            criterios = st.text_area("Critérios que devem manter-se:", key="criterios")
            quando_vendo = st.text_area("Quando é que vendo?", key="quando_vendo")
            decisao = st.selectbox("Decisão final", ["✅ Comprar", "⏳ Aguardar", "❌ Não comprar"], key="decisao")

        if decisao == "✅ Comprar":
            st.success(f"Decisão: COMPRAR {ticker.upper()}")
        elif decisao == "⏳ Aguardar":
            st.warning(f"Decisão: AGUARDAR — monitorizar {ticker.upper()}")
        else:
            st.error(f"Decisão: NÃO COMPRAR {ticker.upper()}")

        # ✅ Botão PDF no fim
        botao_pdf()
