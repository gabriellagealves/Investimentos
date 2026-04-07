import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import time

st.set_page_config(page_title="Análise de Ações", layout="wide")

# --- CACHE PARA ALPHA VANTAGE ---
@st.cache_data(ttl=3600)
def obter_dados_alpha_vantage(ticker_symbol, api_key):
    url_is = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker_symbol}&apikey={api_key}"
    res_is = requests.get(url_is).json()
    time.sleep(2)
    url_cf = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker_symbol}&apikey={api_key}"
    res_cf = requests.get(url_cf).json()
    return res_is, res_cf

# --- BARRA LATERAL ---
st.sidebar.header("Configurações")
av_api_key = st.sidebar.text_input("API Key do Alpha Vantage", type="password")
if st.sidebar.button("Limpar Cache"):
    st.cache_data.clear()

st.title("Análise de Ações")
ticker = st.text_input("Ticker da ação (ex: AAPL, AMD)")

if ticker:
    with st.spinner('A processar dados...'):
        acao = yf.Ticker(ticker)
        info = acao.info
        # Puxar balanço e financeiro do yfinance para cálculos manuais
        bs = acao.balance_sheet
        fin = acao.financials

        st.subheader(f"{info.get('longName', 'N/D')} ({ticker.upper()})")
        st.caption(f"Setor: {info.get('sector', 'N/D')} | Indústria: {info.get('industry', 'N/D')}")
        st.divider()

        # ── 1. MACRO E NEGÓCIO (Resumido para o código não ficar gigante) ──
        # ... (Mantém as tuas secções 1, 2 e 3 como tinhas) ...

        # ── 4. QUANTITATIVA ──────────────────────────────────────────────────
        st.header("4. Quantitativa")
        
        # 4.1 Evolução Histórica
        st.subheader("4.1 Evolução: Financeira e Acionária")

        if av_api_key:
            try:
                is_data, cf_data = obter_dados_alpha_vantage(ticker, av_api_key)

                if "annualReports" in is_data and "annualReports" in cf_data:
                    df_is = pd.DataFrame(is_data["annualReports"][:5]).iloc[::-1]
                    df_cf = pd.DataFrame(cf_data["annualReports"][:5]).iloc[::-1]
                    anos = pd.to_datetime(df_is['fiscalDateEnding']).dt.year.astype(str)

                    # Métricas Financeiras
                    rev_hist = pd.to_numeric(df_is['totalRevenue']) / 1e9
                    net_hist = pd.to_numeric(df_is['netIncome']) / 1e9
                    cfo_hist = pd.to_numeric(df_cf['operatingCashflow']) / 1e9
                    fcf_hist = (pd.to_numeric(df_cf['operatingCashflow']) - pd.to_numeric(df_cf['capitalExpenditures'])) / 1e9

                    # Gráficos de Histórico Financeiro
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        fig1 = go.Figure()
                        fig1.add_trace(go.Bar(x=anos, y=rev_hist, name="Receita", marker_color='#1f77b4'))
                        fig1.add_trace(go.Bar(x=anos, y=net_hist, name="Lucro", marker_color='#FFD700'))
                        fig1.update_layout(title="Receita vs Lucro Líquido ($B)", barmode='group', template='plotly_dark')
                        st.plotly_chart(fig1, use_container_width=True)

                    with col_g2:
                        fig2 = go.Figure()
                        fig2.add_trace(go.Bar(x=anos, y=cfo_hist, name="CFO", marker_color='#1f77b4'))
                        fig2.add_trace(go.Bar(x=anos, y=fcf_hist, name="FCF", marker_color='#00CC96'))
                        fig2.update_layout(title="CFO vs Free Cash Flow ($B)", barmode='group', template='plotly_dark')
                        st.plotly_chart(fig2, use_container_width=True)

                    # 4.1.2 Histograma de Ações (Ordinary Shares Number)
                    st.write("### Evolução das Ações em Circulação")
                    if 'Ordinary Shares Number' in bs.index:
                        shares_series = bs.loc['Ordinary Shares Number'].sort_index(ascending=True)
                        anos_shares = shares_series.index.year.astype(str)
                        val_shares = shares_series.values / 1e6 # Milhões de ações

                        fig_shares = go.Figure()
                        fig_shares.add_trace(go.Bar(x=anos_shares, y=val_shares, marker_color='#8E44AD', name="Shares"))
                        fig_shares.update_layout(title="Ordinary Shares Number (Milhões)", template='plotly_dark', height=300)
                        st.plotly_chart(fig_shares, use_container_width=True)
                else:
                    st.warning("Limite de API ou Ticker não encontrado no Alpha Vantage.")
            except Exception as e:
                st.error(f"Erro Alpha Vantage: {e}")

        # 4.2 Métricas de Eficiência e Saúde (CÁLCULOS MANUAIS)
        st.divider()
        st.subheader("4.2 Eficiência, ROIC e Liquidez")
        
        col1, col2, col3, col4 = st.columns(4)

        # --- CÁLCULO ROIC ---
        try:
            ebit = fin.loc['EBIT'].iloc
            tax_provision = fin.loc['Tax Provision'].iloc
            net_income_before_tax = fin.loc['Pretax Income'].iloc
            tax_rate = tax_provision / net_income_before_tax if net_income_before_tax > 0 else 0.21
            nopat = ebit * (1 - tax_rate)
            
            invested_capital = (bs.loc['Total Assets'].iloc - bs.loc['Current Liabilities'].iloc) 
            roic = (nopat / invested_capital) * 100
            col1.metric("ROIC (Manual)", f"{roic:.1f}%")
        except:
            col1.metric("ROIC (Manual)", "N/D")

        # --- CÁLCULO CASH CONVERSION CYCLE (CCC) ---
        try:
            inventory = bs.loc['Inventory'].iloc
            cogs = abs(fin.loc['Cost Of Revenue'].iloc)
            receivables = bs.loc['Receivables'].iloc
            revenue = fin.loc['Total Revenue'].iloc
            payables = bs.loc['Accounts Payable'].iloc

            dio = (inventory / cogs) * 365
            dso = (receivables / revenue) * 365
            dpo = (payables / cogs) * 365
            ccc = dio + dso - dpo
            col2.metric("Cash Conv. Cycle", f"{int(ccc)} dias", help=f"DIO: {int(dio)} | DSO: {int(dso)} | DPO: {int(dpo)}")
        except:
            col2.metric("Cash Conv. Cycle", "N/D")

        # --- CÁLCULO INTEREST COVERAGE RATIO ---
        try:
            ebit = fin.loc['EBIT'].iloc
            interest_exp = abs(fin.loc['Interest Expense'].iloc)
            if interest_exp > 0:
                icr = ebit / interest_exp
                col3.metric("Interest Coverage", f"{icr:.1f}x")
            else:
                col3.metric("Interest Coverage", "Seguro (Sem Dívida)")
        except:
            col3.metric("Interest Coverage", "N/D")

        # Margem Líquida (yfinance)
        mn = info.get("profitMargins", 0) * 100
        col4.metric("Margem Líquida", f"{mn:.1f}%")

        # ... (Mantém o resto das tuas secções 5 e 6) ...
