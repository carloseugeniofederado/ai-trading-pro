# AI TRADING PRO — versão inicial

## O que esta versão faz
- Consulta dados de mercado através do Yahoo Finance.
- Mostra gráficos de velas e médias móveis.
- Calcula RSI e MACD.
- Produz um sinal experimental BUY / SELL / HOLD.
- Inclui um simulador educativo de Stop Loss e Take Profit.

## Limitações importantes
- Os dados podem ter atraso, limites ou falhas e não são dados garantidos de execução.
- A pontuação de confiança é heurística, não uma probabilidade validada.
- Não existe ligação a corretoras nem execução de ordens.
- Não utilizar esta versão para decidir operações com dinheiro real.

## Publicar no Streamlit Community Cloud
1. Extrai o ZIP.
2. Cria um repositório no GitHub e envia `app.py` e `requirements.txt`.
3. No Streamlit Community Cloud, escolhe **New app**.
4. Selecciona o repositório, a branch e o ficheiro `app.py`.
5. Carrega em **Deploy**.

O ficheiro `requirements.txt` instala as dependências automaticamente.
