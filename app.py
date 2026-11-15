import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone

st.set_page_config(page_title="AI TRADING PRO", page_icon="📈", layout="wide")

st.markdown("""
<style>
.stApp {background: #0b1020; color: #f5f7fb;}
[data-testid="stMetric"] {background:#151d32; padding:14px; border-radius:12px;}
h1,h2,h3 {color:#f5f7fb;}
</style>
""", unsafe_allow_html=True)

st.title("📈 AI TRADING PRO")
st.caption("Análise de mercado e sinais experimentais — não é aconselhamento financeiro.")

ASSETS = {
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Solana (SOL)": "SOL-USD",
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "S&P 500 ETF (SPY)": "SPY",
    "Nasdaq 100 ETF (QQQ)": "QQQ",
    "Vanguard S&P 500 (VOO)": "VOO",
}

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=60)
def load_data(ticker, period, interval):
    return yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)

with st.sidebar:
    st.header("⚙️ Configuração")
    asset_name = st.selectbox("Escolhe um activo", list(ASSETS.keys()))
    ticker = ASSETS[asset_name]
    period = st.selectbox("Período", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=3)
    interval = st.selectbox("Intervalo do gráfico", ["5m", "15m", "30m", "1h", "1d"], index=4)
    if st.button("🔄 Actualizar dados"):
        st.cache_data.clear()

st.info("Os dados são obtidos através do Yahoo Finance e podem ter atrasos, limites ou indisponibilidade. Não são garantidos como dados de execução de uma corretora.")

try:
    df = load_data(ticker, period, interval)
    if df is None or df.empty:
        st.error("Não foi possível obter dados para este activo/período. Tenta outra opção.")
        st.stop()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    required = ["Open", "High", "Low", "Close", "Volume"]
    df = df[[c for c in required if c in df.columns]].dropna()
    if "Close" not in df or len(df) < 30:
        st.error("Dados insuficientes para calcular os indicadores.")
        st.stop()

    close = df["Close"]
    df["EMA20"] = close.ewm(span=20, adjust=False).mean()
    df["EMA50"] = close.ewm(span=50, adjust=False).mean()
    df["RSI"] = rsi(close)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last["Close"])
    rsi_value = float(last["RSI"]) if pd.notna(last["RSI"]) else 50.0

    score = 0
    score += 1 if last["EMA20"] > last["EMA50"] else -1
    score += 1 if last["MACD"] > last["MACD_signal"] else -1
    score += 1 if price > last["EMA20"] else -1
    if rsi_value > 70:
        score -= 1
    elif rsi_value < 30:
        score += 1

    if score >= 2:
        signal = "BUY 🟢"
        explanation = "Os indicadores seleccionados mostram tendência positiva. Confirma sempre antes de agir."
    elif score <= -2:
        signal = "SELL 🔴"
        explanation = "Os indicadores seleccionados mostram tendência negativa. Confirma sempre antes de agir."
    else:
        signal = "HOLD 🟡"
        explanation = "Os indicadores estão mistos; pode ser melhor aguardar por confirmação."

    confidence = min(85, 50 + abs(score) * 8)
    change = ((price / float(prev["Close"])) - 1) * 100 if float(prev["Close"]) else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Activo", asset_name)
    c2.metric("Último preço", f"${price:,.4f}")
    c3.metric("Variação da última vela", f"{change:+.2f}%")
    c4.metric("RSI (14)", f"{rsi_value:.1f}")

    st.subheader("Sinal experimental")
    s1, s2 = st.columns([1, 2])
    s1.metric("Sinal", signal)
    s1.metric("Pontuação dos indicadores", f"{score}/4")
    s2.metric("Confiança indicativa do modelo", f"{confidence}%")
    s2.write(explanation)
    st.caption("A percentagem acima é uma pontuação heurística, NÃO uma probabilidade estatística nem garantia de acerto.")

    st.subheader("Gráfico de preços")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Preço"))
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA 20"))
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], name="EMA 50"))
    fig.update_layout(template="plotly_dark", height=520, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Indicadores")
    i1, i2 = st.columns(2)
    with i1:
        st.write("RSI")
        rf = go.Figure()
        rf.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI"))
        rf.add_hline(y=70, line_dash="dash")
        rf.add_hline(y=30, line_dash="dash")
        rf.update_layout(template="plotly_dark", height=260, yaxis_range=[0,100])
        st.plotly_chart(rf, use_container_width=True)
    with i2:
        st.write("MACD")
        mf = go.Figure()
        mf.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD"))
        mf.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], name="Sinal"))
        mf.update_layout(template="plotly_dark", height=260)
        st.plotly_chart(mf, use_container_width=True)

    st.subheader("Simulador educativo de risco")
    entry = st.number_input("Preço de entrada hipotético", value=float(price), min_value=0.000001, format="%.6f")
    risk_pct = st.slider("Stop Loss (%)", 0.5, 10.0, 2.0, 0.5)
    reward_ratio = st.slider("Relação risco/retorno", 1.0, 5.0, 2.0, 0.5)
    stop = entry * (1 - risk_pct/100)
    target = entry * (1 + (risk_pct * reward_ratio)/100)
    a, b = st.columns(2)
    a.metric("Stop Loss hipotético", f"${stop:,.6f}")
    b.metric("Take Profit hipotético", f"${target:,.6f}")
    st.caption("Cálculo ilustrativo para posição comprada. Não envia ordens e não considera taxas, slippage ou volatilidade futura.")

    st.subheader("Dados recentes")
    st.dataframe(df.tail(15).sort_index(ascending=False), use_container_width=True)

    st.caption(f"Última observação recebida: {df.index[-1]}. Actualização em cache até 60 segundos.")
except Exception as e:
    st.error("Ocorreu um erro ao carregar ou analisar os dados.")
    st.code(str(e))
    st.caption("Verifica a ligação à internet e tenta novamente mais tarde.")

st.divider()
st.warning("⚠️ Esta versão é apenas para estudo. Não está ligada a uma corretora, não executa operações e não deve ser usada como única base para decisões com dinheiro real.")
