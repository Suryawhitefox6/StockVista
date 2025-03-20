import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME, STOCKS

# Connect directly to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


# Function to load stock data from MongoDB
def load_stock_data(ticker=None, start_date=None, end_date=None):
    query = {}
    if ticker:
        query["Ticker"] = ticker
    if start_date and end_date:
        query["Timestamp"] = {"$gte": start_date, "$lte": end_date}

    cursor = collection.find(query)
    df = pd.DataFrame(list(cursor))
    return df


# Function to compute RSI
def compute_rsi(df, period=14):
    delta = df["Close"].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1("Real-Time & Historical Stock Analytics"),

    dcc.Dropdown(
        id="stock-dropdown",
        options=[{"label": stock, "value": stock} for stock in STOCKS],
        value=STOCKS[0],
        clearable=False
    ),

    dcc.DatePickerRange(
        id='date-picker-range',
        start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d'),
        display_format='YYYY-MM-DD'
    ),

    dcc.Tabs(id="tabs", value='tab1', children=[
        dcc.Tab(label='Price Analysis', value='tab1'),
        dcc.Tab(label='Top Gainers & Losers', value='tab2'),
        dcc.Tab(label='Volume Analysis', value='tab3'),
        dcc.Tab(label='Moving Averages', value='tab4'),
        dcc.Tab(label='RSI Analysis', value='tab5'),
        dcc.Tab(label='Overall Analysis', value='tab6')
    ]),

    html.Div(id='tabs-content'),
])


@app.callback(
    Output('tabs-content', 'children'),
    [Input("tabs", "value"),
     Input("stock-dropdown", "value"),
     Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_tab(tab, selected_stock, start_date, end_date):
    df = load_stock_data(selected_stock, start_date, end_date)
    if df.empty:
        return html.Div("No data available for the selected criteria")

    def generate_table(dataframe, columns):
        return html.Table([
            html.Thead(html.Tr([html.Th(col) for col in columns])),
            html.Tbody([
                html.Tr([html.Td(row[col]) for col in columns]) for _, row in dataframe.iterrows()
            ])
        ], style={'border': '1px solid black', 'textAlign': 'center', 'borderCollapse': 'collapse'})

    if tab == 'tab1':  # Price Analysis
        fig = go.Figure([go.Scatter(x=df["Timestamp"], y=df["Close"], mode="lines", name="Close Price")])
        fig.update_layout(title=f"Price Analysis for {selected_stock}", xaxis_title="Time", yaxis_title="Price")
        table = generate_table(df, ["Timestamp", "Close"])
        return html.Div([dcc.Graph(figure=fig), table])

    elif tab == 'tab2':  # Top Gainers & Losers
        df_all = load_stock_data(start_date=start_date, end_date=end_date)
        if df_all.empty:
            return html.Div("No data available for the selected date range")

        tickers = df_all["Ticker"].unique()
        result_data = []

        for ticker in tickers:
            ticker_data = df_all[df_all["Ticker"] == ticker].sort_values("Timestamp")
            if len(ticker_data) >= 2:
                first_close = ticker_data["Close"].iloc[0]
                last_close = ticker_data["Close"].iloc[-1]
                change_pct = ((last_close - first_close) / first_close) * 100
                result_data.append({"Ticker": ticker, "Change": round(change_pct, 2)})

        change_df = pd.DataFrame(result_data).sort_values(by="Change", ascending=False)
        gainers = change_df.head(10)
        losers = change_df.tail(10).sort_values(by="Change")

        return html.Div([
            dcc.Graph(figure=px.bar(gainers, x='Ticker', y='Change', title="Top Gainers", color='Change')),
            generate_table(gainers, ["Ticker", "Change"]),
            dcc.Graph(figure=px.bar(losers, x='Ticker', y='Change', title="Bottom Performers", color='Change')),
            generate_table(losers, ["Ticker", "Change"])
        ])

    elif tab == 'tab3':  # Volume Analysis
        fig = go.Figure([go.Bar(x=df["Timestamp"], y=df["Volume"], name="Volume")])
        fig.update_layout(title=f"Volume Analysis for {selected_stock}", xaxis_title="Time", yaxis_title="Volume")
        table = generate_table(df, ["Timestamp", "Volume"])
        return html.Div([dcc.Graph(figure=fig), table])

    elif tab == 'tab4':  # Moving Averages
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["SMA_200"] = df["Close"].rolling(window=200).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["Close"], mode="lines", name="Close Price"))
        fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["SMA_50"], mode="lines", name="SMA 50"))
        fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["SMA_200"], mode="lines", name="SMA 200"))

        table = generate_table(df, ["Timestamp", "Close", "SMA_50", "SMA_200"])
        return html.Div([dcc.Graph(figure=fig), table])

    elif tab == 'tab5':  # RSI Analysis
        df = compute_rsi(df)
        fig = go.Figure([go.Scatter(x=df["Timestamp"], y=df["RSI"], mode="lines", name="RSI")])
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig.update_layout(title=f"RSI Analysis for {selected_stock}", xaxis_title="Time", yaxis_title="RSI Value")
        table = generate_table(df, ["Timestamp", "RSI"])
        return html.Div([dcc.Graph(figure=fig), table])

    elif tab == 'tab6':  # Overall Analysis
        df = compute_rsi(df)
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["SMA_200"] = df["Close"].rolling(window=200).mean()

        return html.Div([
            update_tab('tab1', selected_stock, start_date, end_date),
            update_tab('tab3', selected_stock, start_date, end_date),
            update_tab('tab4', selected_stock, start_date, end_date),
            update_tab('tab5', selected_stock, start_date, end_date),
        ])


if __name__ == "__main__":
    app.run(debug=True, port=8050)
