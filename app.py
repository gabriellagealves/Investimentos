import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Análise de Ações", layout="wide")
st.title("Análise de Ações")

ticker = st.text_input("Ticker da ação (ex: AAPL, MSFT, NVDA, AMD)")

if ticker:
    acao = yf.Ticker(ticker)
    info = acao.info

    nome = info.get("longName", "N/D")
    st.subheader(f"{nome} ({ticker.upper()})")
    st.caption(f"Setor: {info.get('sector', 'N/D')} | Indústria: {info.get('industry', 'N/D')} | País: {info.get('country', 'N/D')}")

    st.divider()

    # ── 1. MACRO E SETORIAL ──────────────────────────────────────────────
    st.header("1. Macro e Setorial")
    col1, col2, col3 = st.columns(3)
    with col1:
        tendencia = st.selectbox("Tendência do índice", ["Bull", "Bear", "Lateral"])
    with col2:
        sentimento = st.selectbox("Sentimento Mundial", ["Bull", "Bear", "Lateral"])
    with col3:
        pais = st.text_input("País", value=info.get("country", ""))

    st.divider()

    # ── 2. NEGÓCIO / EMPRESA ─────────────────────────────────────────────
    st.header("2. Negócio / Empresa")

    descricao = info.get("longBusinessSummary", "")
    if descricao:
        with st.expander("Descrição do negócio (fonte: Yahoo Finance)"):
            st.write(descricao)

    col1, col2 = st.columns(2)
    with col1:
        o_que_vende = st.text_area("O que vende?")
        onde_opera = st.text_input("Onde opera?", value=info.get("country", ""))
    with col2:
        como_ganha = st.text_area("Como ganha dinheiro?")
        lider = st.selectbox("É líder de mercado?", ["Sim", "Não", "Parcialmente"])

    st.divider()

    # ── 3. QUALITATIVA E RISCO ───────────────────────────────────────────
    st.header("3. Qualitativa e Risco")

    col1, col2 = st.columns(2)
    with col1:
        moat = st.selectbox("Tem MOAT?", ["Sim", "Não", "Parcialmente"])
        moat_desc = st.text_area("Descreve o MOAT:")
        lideranca = st.text_area("Liderança (CEO, diretores):")
    with col2:
        visao = st.text_area("Visão estratégica da gestão:")
        acoes_empresa = st.selectbox("Ações da empresa (buybacks?)", ["Sim - reduz ações", "Não", "Dilui acionistas"])
        riscos = st.text_area("Riscos identificados:")

    st.divider()

 # ── 4. QUANTITATIVA ──────────────────────────────────────────────────
    st.header("4. Quantitativa")

    # 4.1 Evolução Histórica e TTM
    st.subheader("4.1 Gráficos de Evolução (Anual vs TTM)")

    try:
        # --- PREPARAÇÃO DOS DADOS ---
        df_fin = acao.financials.T.sort_index(ascending=True)
        df_cf = acao.cashflow.T.sort_index(ascending=True)
        
        # Criamos o índice de anos (ex: 2021, 2022...)
        anos = df_fin.index.year.astype(str)

        # Dados TTM extraídos do 'info'
        ttm_label = ['TTM']
        ttm_rev = [info.get("totalRevenue", 0) / 1e9]
        ttm_net = [info.get("netIncomeToCommon", 0) / 1e9]
        ttm_ebitda = [info.get("ebitda", 0) / 1e9]
        ttm_cfo = [info.get("operatingCashflow", 0) / 1e9]
        ttm_fcf = [info.get("freeCashflow", 0) / 1e9]

        # --- GRÁFICO 1: RECEITA VS LUCRO ---
        fig1 = go.Figure()
        # Se a coluna não existir, cria uma lista de zeros
        rev_hist = df_fin['Total Revenue']/1e9 if 'Total Revenue' in df_fin.columns else * len(anos)
        net_hist = df_fin['Net Income']/1e9 if 'Net Income' in df_fin.columns else * len(anos)
        
        fig1.add_trace(go.Bar(x=anos, y=rev_hist, name='Receita', marker_color='#1f77b4'))
        fig1.add_trace(go.Bar(x=anos, y=net_hist, name='Lucro Líquido', marker_color='#FFD700'))
        
        fig1.add_trace(go.Bar(x=ttm_label, y=ttm_rev, name='Receita (TTM)', marker_color='#1f77b4', opacity=0.6, showlegend=False))
        fig1.add_trace(go.Bar(x=ttm_label, y=ttm_net, name='Lucro (TTM)', marker_color='#FFD700', opacity=0.6, showlegend=False))
        fig1.update_layout(title="Receita vs Lucro Líquido ($B)", barmode='group', template='plotly_dark', height=350)

        # --- GRÁFICO 2: CFO VS FCF ---
        fig2 = go.Figure()
        # CORREÇÃO AQUI: Adicionado o antes do * len(anos)
        cfo_hist = df_cf['Operating Cash Flow']/1e9 if 'Operating Cash Flow' in df_cf.columns else * len(anos)
        fcf_hist = df_cf['Free Cash Flow']/1e9 if 'Free Cash Flow' in df_cf.columns else * len(anos)
        
        fig2.add_trace(go.Bar(x=anos, y=cfo_hist, name='CFO', marker_color='#1f77b4'))
        fig2.add_trace(go.Bar(x=anos, y=fcf_hist, name='FCF', marker_color='#FFD700'))
        
        fig2.add_trace(go.Bar(x=ttm_label, y=ttm_cfo, name='CFO (TTM)', marker_color='#1f77b4', opacity=0.6, showlegend=False))
        fig2.add_trace(go.Bar(x=ttm_label, y=ttm_fcf, name='FCF (TTM)', marker_color='#FFD700', opacity=0.6, showlegend=False))
        fig2.update_layout(title="CFO vs Free Cash Flow ($B)", barmode='group', template='plotly_dark', height=350)

        # --- GRÁFICO 3: EBITDA ---
        fig3 = go.Figure()
        # CORREÇÃO AQUI: Adicionado o antes do * len(anos)
        ebitda_hist = df_fin['EBITDA'] / 1e9 if 'EBITDA' in df_fin.columns else * len(anos)
        
        fig3.add_trace(go.Bar(x=anos, y=ebitda_hist, name='EBITDA', marker_color='#00CC96'))
        fig3.add_trace(go.Bar(x=ttm_label, y=ttm_ebitda, name='EBITDA (TTM)', marker_color='#00CC96', opacity=0.6, showlegend=False))
        fig3.update_layout(title="EBITDA ($B)", template='plotly_dark', height=350)

        # Exibição
        st.plotly_chart(fig1, use_container_width=True)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(fig2, use_container_width=True)
        with col_g2:
            st.plotly_chart(fig3, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar gráficos: {e}")

    st.divider()
    
    # --- MÉTRICAS DE RESUMO (O que tinhas antes + CCR) ---
    st.subheader("Métricas Atuais e Crescimento")
    
    c1, c2, c3, c4 = st.columns(4)
    
    cfo_val = info.get("operatingCashflow", None)
    c1.metric("Cash from Operations (CFO)", f"${cfo_val/1e9:.1f}B" if cfo_val else "N/D")

    rev_growth = info.get("revenueGrowth", None)
    c2.metric("Crescimento Receita (YoY)", f"{rev_growth*100:.1f}%" if rev_growth else "N/D")

    earn_growth = info.get("earningsGrowth", None)
    c3.metric("Crescimento Lucro (YoY)", f"{earn_growth*100:.1f}%" if earn_growth else "N/D")

    # Cálculo do CCR (Cash Conversion Ratio)
    lucro_val = info.get("netIncomeToCommon", None)
    fcf_val = info.get("freeCashflow", None)
    if fcf_val and lucro_val and lucro_val != 0:
        ccr = fcf_val / lucro_val
        c4.metric("CCR (FCF / Lucro)", f"{ccr:.2f}x")
    else:
        c4.metric("CCR (FCF / Lucro)", "N/D")

     # Manter os indicadores atuais (métricas de resumo)
    st.subheader("Métricas Atuais de Crescimento")
    
    col1, col2, col3 = st.columns(3)
    cfo = info.get("operatingCashflow", None)
    col1.metric("Cash from Operations (CFO)", f"${cfo/1e9:.1f}B" if cfo else "N/D")

    crescimento_receita = info.get("revenueGrowth", None)
    col2.metric("Crescimento Receita (YoY)", f"{crescimento_receita*100:.1f}%" if crescimento_receita else "N/D")

    crescimento_lucro = info.get("earningsGrowth", None)
    col3.metric("Crescimento Lucro (YoY)", f"{crescimento_lucro*100:.1f}%" if crescimento_lucro else "N/D")

    # 4.2 Performance
    st.subheader("4.2 Métricas de Performance")
    col1, col2, col3, col4, col5 = st.columns(5)

    mg = info.get("grossMargins", None)
    col1.metric("Margem Bruta", f"{mg*100:.1f}%" if mg else "N/D")

    mo = info.get("operatingMargins", None)
    col2.metric("Margem Operacional", f"{mo*100:.1f}%" if mo else "N/D")

    mn = info.get("profitMargins", None)
    col3.metric("Margem Líquida", f"{mn*100:.1f}%" if mn else "N/D")

    roe = info.get("returnOnEquity", None)
    col4.metric("ROE", f"{roe*100:.1f}%" if roe else "N/D")

    roic = info.get("returnOnAssets", None)
    col5.metric("ROA (aprox. ROIC)", f"{roic*100:.1f}%" if roic else "N/D")

    # 4.3 Saúde Financeira
    st.subheader("4.3 Saúde Financeira")
    col1, col2, col3, col4 = st.columns(4)

    divida = info.get("totalDebt", None)
    ebitda_val = info.get("ebitda", None)
    if divida and ebitda_val and ebitda_val != 0:
        debt_ebitda = divida / ebitda_val
        col1.metric("DEBT / EBITDA", f"{debt_ebitda:.1f}x")
    else:
        col1.metric("DEBT / EBITDA", "N/D")

    icr = info.get("ebitToInterestExpense", None)
    col2.metric("Interest Coverage Ratio", f"{icr:.1f}x" if icr else "N/D")

    cr = info.get("currentRatio", None)
    col3.metric("Current Ratio", f"{cr:.2f}" if cr else "N/D")

    if divida and fcf and fcf != 0:
        debt_fcf = divida / fcf
        col4.metric("Total DEBT / FCF", f"{debt_fcf:.1f}x")
    else:
        col4.metric("Total DEBT / FCF", "N/D")

    # 4.4 Alavancagem
    st.subheader("4.4 Alavancagem Financeira")
    col1, col2 = st.columns(2)

    de = info.get("debtToEquity", None)
    col1.metric("DEBT / EQUITY", f"{de:.1f}" if de else "N/D")

    col2.metric("Dívida Total", f"${divida/1e9:.1f}B" if divida else "N/D")

    # 4.5 Dividendos
    st.subheader("4.5 Dividendos")
    col1, col2, col3 = st.columns(3)

    div_yield = info.get("dividendYield", None)
    col1.metric("Dividend Yield", f"{div_yield*100:.2f}%" if div_yield else "N/D")

    payout = info.get("payoutRatio", None)
    col2.metric("Payout Ratio", f"{payout*100:.1f}%" if payout else "N/D")

    shares = info.get("sharesOutstanding", None)
    col3.metric("Ações em Circulação", f"{shares/1e9:.2f}B" if shares else "N/D")

    # 4.6 Valuation
    st.subheader("4.6 Valuation")
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
        valor_intriseco = st.number_input("Valor Intrínseco Estimado ($)", min_value=0.0, step=0.5)
    with col2:
        if valor_intriseco > 0 and preco_atual:
            margem = ((valor_intriseco - preco_atual) / valor_intriseco) * 100
            col2.metric("Margem de Segurança", f"{margem:.1f}%",
                       delta="Subvalorizada" if margem > 0 else "Sobrevalorizada")

    st.divider()

    # ── 6. CONCLUSÃO FINAL ───────────────────────────────────────────────
    st.header("6. Conclusão Final")

    col1, col2 = st.columns(2)
    with col1:
        data_analise = st.date_input("Data da análise")
        motivo_compra = st.text_area("Motivo principal da compra:")
        periodo = st.selectbox("Período de investimento", ["Curto prazo (<1 ano)", "Médio prazo (1-3 anos)", "Longo prazo (>3 anos)"])
    with col2:
        criterios = st.text_area("Critérios que devem manter-se:")
        quando_vendo = st.text_area("Quando é que vendo?")
        decisao = st.selectbox("Decisão final", ["✅ Comprar", "⏳ Aguardar", "❌ Não comprar"])

    if decisao == "✅ Comprar":
        st.success(f"Decisão: COMPRAR {ticker.upper()}")
    elif decisao == "⏳ Aguardar":
        st.warning(f"Decisão: AGUARDAR — monitorizar {ticker.upper()}")
    else:
        st.error(f"Decisão: NÃO COMPRAR {ticker.upper()}")
