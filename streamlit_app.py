import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(page_title="Robô de Swing Trade - B3", layout="wide")
st.title("📊 Robô de Swing Trade - Ações BR (Simulado)")

# Sidebar - Parâmetros da estratégia
st.sidebar.header("Parâmetros da Estratégia")
ticker = st.sidebar.text_input("Ticker (ex: PETR4.SA)", value="PETR4.SA")
periodo = st.sidebar.selectbox("Período", ["3mo", "6mo", "1y"], index=0)
intervalo = st.sidebar.selectbox("Intervalo", ["1d", "1h"], index=0)

rsi_window = st.sidebar.slider("RSI - Período", 2, 30, 14)
mme_period = st.sidebar.slider("Média Móvel Exponencial (MME)", 5, 50, 20)

st.sidebar.markdown("---")
capital_inicial = st.sidebar.number_input("Capital Inicial (simulado)", value=10000.0)

# Download de dados
df = yf.download(ticker, period=periodo, interval=intervalo)

if df.empty:
    st.error("Erro ao buscar os dados. Verifique o ticker e tente novamente.")
    st.stop()

# Preencher possíveis valores NaN na coluna Close
df['Close'] = df['Close'].fillna(method='ffill').fillna(method='bfill')

# Garantir que 'Close' é uma Series 1D para o RSI
close_prices = df['Close'].squeeze()

# Calcular RSI e MME
df['RSI'] = ta.momentum.RSIIndicator(close_prices, window=rsi_window).rsi()
df['MME'] = close_prices.ewm(span=mme_period).mean()

# Função para extrair valor escalar com segurança
def get_scalar(val):
    try:
        return val.item()
    except:
        return val

# Sinal atual corrigido para evitar erro
ultima_linha = df.iloc[-1]
rsi_val = get_scalar(ultima_linha['RSI'])
close_val = get_scalar(ultima_linha['Close'])
mme_val = get_scalar(ultima_linha['MME'])

sinal = "AGUARDAR"
if rsi_val < 30 and close_val > mme_val:
    sinal = "📈 COMPRA"
elif rsi_val > 70 or close_val < mme_val:
    sinal = "🔻 VENDA"

# Gráfico
st.subheader(f"Gráfico de Preço - {ticker}")
st.line_chart(df[['Close', 'MME']])

# Exibição do RSI
df_indicadores = df[['Close', 'RSI', 'MME']].copy()
df_indicadores.dropna(inplace=True)
st.subheader("Indicadores Técnicos")
st.dataframe(df_indicadores.tail(10))

# Sinal Atual
st.subheader("Sinal Atual")
st.markdown(f"### {sinal}")

# Simulador de trade simples (paper trading)
comprado = False
preco_entrada = 0
capital = capital_inicial
posicao = 0
trades = []

for i in range(1, len(df)):
    row = df.iloc[i]
    rsi = row['RSI']
    close = row['Close']
    mme = row['MME']

    if not comprado and rsi < 30 and close > mme:
        preco_entrada = close
        posicao = capital // preco_entrada
        capital -= posicao * preco_entrada
        comprado = True
        trades.append((row.name, "COMPRA", preco_entrada))

    elif comprado and (rsi > 70 or close < mme):
        capital += posicao * close
        trades.append((row.name, "VENDA", close))
        comprado = False
        posicao = 0

# Resultado Final
lucro = capital + (posicao * df.iloc[-1]['Close'] if comprado else 0) - capital_inicial
st.subheader("Resumo do Trade (Simulado)")
st.write(f"Trades realizados: {len(trades)}")
st.write(f"Lucro/prejuízo: R$ {lucro:.2f}")

# Exibir trades
if trades:
    trade_df = pd.DataFrame(trades, columns=["Data", "Tipo", "Preço"])
    st.dataframe(trade_df)
