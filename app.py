import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import time

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

        st.divider()

        # ── 1. MACRO E SETORIAL ──────────────────────────────────────────────
        st.header("1. Macro e Setorial")
        
        # Criamos 5 colunas para manter tudo na mesma linha
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.write("Tendência do índice")
            tendencia = st.selectbox("Qual a tendência do mercado/índice?", ["Preencher", "Bull", "Bear", "Lateral"])
        
        with col2:
            st.write("Sentimento Mundial")
            sentimento = st.selectbox("Qual é a saúde económica global?", ["Preencher", "Bull", "Bear", "Lateral"])
            
        with col3:
            st.write("País")
            sit_pais = st.selectbox("Situação económica do país/região?", ["Preencher", "Expansão", "Pico/ Auge", "Recessão", "Recuperação"])
            
        with col4:
            st.markdown("&nbsp;")
            estabilidade = st.selectbox("É estável, transparente e estimulada?", ["Preencher", "Sim", "Não"])
            
        with col5:
            st.markdown("&nbsp;")
            pib_emprego = st.selectbox("PIB e mercado de trabalho?", ["Preencher", "Bom", "Moderado", "Mau"])

        st.divider()

        # ── 2. NEGÓCIO / EMPRESA ─────────────────────────────────────────────
        st.header("2. Negócio / Empresa")

        descricao = info.get("longBusinessSummary", "")
        if descricao:
            with st.expander("Descrição do negócio (fonte: Yahoo Finance)"):
                st.write(descricao)

        col1, col2 = st.columns(2)
        with col1:
            o_que_vende = st.text_area("O que vende?", placeholder="Explicar numa frase curta")
            onde_opera = st.text_input("Onde opera?", placeholder="Explicar numa frase curta")
        with col2:
            como_ganha = st.text_area("Como ganha dinheiro?", placeholder="Explicar numa frase curta")
            lider = st.selectbox("É líder de mercado?", ["Preencher", "Sim", "Não"])

            # Alinhamento corrigido (as condições ficam dentro da coluna 2)
            if lider == "Sim":
                qual_lider = st.text_input("Qual?", placeholder="Indicar qual o mercado")
            elif lider == "Não":
                quem_lider = st.text_input("Qual é?", placeholder="Indicar o ticker da concorrente")

        st.divider()

        # ── 3. QUALITATIVA E RISCO ───────────────────────────────────────────
        st.header("3. Qualitativa e Risco")

        col1, col2 = st.columns(2)
        with col1:
            # Corrigido o erro do parêntesis a mais
            moat = st.selectbox("Tem MOAT?", ["Preencher", "Sim", "Não"])
            
            if moat == "Sim":
                moat_desc = st.text_area("Descreve o MOAT:", placeholder="Tem uma marca forte? Tem custos de mudança altos? Possui efeitos de rede? (melhora com mais utilizadores)")
            
            lideranca = st.text_area("Liderança (CEO, diretores):")
        with col2:
            visao = st.text_area("Visão estratégica da gestão:")
            acoes_empresa = st.selectbox("Ações da empresa (buybacks?)", ["Sim - reduz ações", "Não", "Dilui acionistas"])
            riscos = st.text_area("Riscos identificados:")

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
                        fig_res = go.Figure()
                        fig_res.add_trace(go.Bar(x=anos_fin, y=rev_hist, name='Receita', marker_color='#1f77b4', text=rev_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_res.add_trace(go.Bar(x=anos_fin, y=net_hist, name='Lucro Líquido', marker_color='#FFD700', text=net_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_res.add_trace(go.Bar(x=['TTM'], y=[ttm_rev], name='Receita (TTM)', marker_color='#1f77b4', opacity=0.6, showlegend=False, text=[f"{ttm_rev:.1f}"], textposition='auto', textfont=dict(color='white')))
                        fig_res.add_trace(go.Bar(x=['TTM'], y=[ttm_net], name='Lucro (TTM)', marker_color='#FFD700', opacity=0.6, showlegend=False, text=[f"{ttm_net:.1f}"], textposition='auto', textfont=dict(color='white')))
                        
                        fig_res.update_layout(title="Receita vs Lucro Líquido", barmode='group', template='plotly_dark', height=400, margin=dict(t=50, b=20), yaxis_title="Biliões de USD ($B)", yaxis_title_font_size=16, bargap=0.1)
                        st.plotly_chart(fig_res, use_container_width=True)

                    with col_g2:
                        fig_cf = go.Figure()
                        fig_cf.add_trace(go.Bar(x=anos_cf, y=cfo_hist, name='CFO', marker_color='#FF9F1C', text=cfo_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_cf.add_trace(go.Bar(x=anos_cf, y=fcf_hist, name='FCF', marker_color='#2EC4B6', text=fcf_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white')))
                        fig_cf.add_trace(go.Bar(x=['TTM'], y=[ttm_cfo], name='CFO (TTM)', marker_color='#FF9F1C', opacity=0.6, showlegend=False, text=[f"{ttm_cfo:.1f}"], textposition='auto', textfont=dict(color='white')))
                        fig_cf.add_trace(go.Bar(x=['TTM'], y=[ttm_fcf], name='FCF (TTM)', marker_color='#2EC4B6', opacity=0.6, showlegend=False, text=[f"{ttm_fcf:.1f}"], textposition='auto', textfont=dict(color='white')))
                        
                        fig_cf.update_layout(title="Cash From Operations (CFO) vs Free Cash Flow (FCF)", barmode='group', template='plotly_dark', height=400, margin=dict(t=50, b=20), yaxis_title="Biliões de USD ($B)", yaxis_title_font_size=16, bargap=0.1)
                        st.plotly_chart(fig_cf, use_container_width=True)

                    with col_g3:
                        fig_ebitda = go.Figure()
                        fig_ebitda.add_trace(go.Bar(x=anos_fin, y=ebitda_hist, name='EBITDA', marker_color='#00CC96', text=ebitda_hist.apply(lambda x: f"{x:.1f}"), textposition='auto', textfont=dict(color='white'))) 
                        fig_ebitda.add_trace(go.Bar(x=['TTM'], y=[ttm_ebitda], name='EBITDA (TTM)', marker_color='#00CC96', opacity=0.6, showlegend=False, text=[f"{ttm_ebitda:.1f}"], textposition='auto', textfont=dict(color='white')))
                        
                        fig_ebitda.update_layout(title="EBITDA", template='plotly_dark', height=280, margin=dict(t=50, b=20), yaxis_title="Biliões de USD ($B)", yaxis_title_font_size=16, bargap=0.6)
                        st.plotly_chart(fig_ebitda, use_container_width=True)

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
            inventory = bs.loc['Inventory'].iloc if 'Inventory' in bs.index else 0
            cogs = abs(fin.loc['Cost Of Revenue'].iloc) if 'Cost Of Revenue' in fin.index else 0
            receivables = bs.loc['Accounts Receivable'].iloc if 'Accounts Receivable' in bs.index else (bs.loc['Receivables'].iloc if 'Receivables' in bs.index else 0)
            revenue = fin.loc['Total Revenue'].iloc
            payables = bs.loc['Accounts Payable'].iloc if 'Accounts Payable' in bs.index else 0

            if cogs > 0 and revenue > 0:
                dio = (inventory / cogs) * 365
                dso = (receivables / revenue) * 365
                dpo = (payables / cogs) * 365
                ccc = dio + dso - dpo
                col3.metric("Cash Conv. Cycle (CCC)", f"{int(ccc)} dias")
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
            ebit = fin.loc['EBIT'].iloc
            tax_provision = fin.loc['Tax Provision'].iloc if 'Tax Provision' in fin.index else 0
            pretax_income = fin.loc['Pretax Income'].iloc if 'Pretax Income' in fin.index else ebit
            
            tax_rate = tax_provision / pretax_income if pretax_income > 0 else 0.21
            nopat = ebit * (1 - tax_rate)
            
            total_assets = bs.loc['Total Assets'].iloc
            current_liab = bs.loc['Current Liabilities'].iloc if 'Current Liabilities' in bs.index else 0
            invested_capital = total_assets - current_liab
            
            roic_val = (nopat / invested_capital) * 100
            col5.metric("ROIC", f"{roic_val:.1f}%")
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
            ebit_val = fin.loc['EBIT'].iloc
            interest_exp = abs(fin.loc['Interest Expense'].iloc) if 'Interest Expense' in fin.index else 0
            
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
