import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px
from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME, STOCKS

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Initialize Dash app
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
        start_date=(datetime.now() - pd.DateOffset(days=7)).date(),
        end_date=datetime.now().date(),
        display_format='YYYY-MM-DD'
    ),

    dcc.Tabs(id="tabs", value='tab1', children=[
        dcc.Tab(label='Price Analysis', value='tab1'),
        dcc.Tab(label='Technical Indicators', value='tab2'),
        dcc.Tab(label='Top Gainers & Losers', value='tab3'),
        dcc.Tab(label='Volume Analysis', value='tab4'),
        dcc.Tab(label='Moving Averages', value='tab5'),
    ]),

    html.Div(id='tabs-content'),

    dcc.Interval(id="interval-update", interval=60000, n_intervals=0)  # Refresh every 1 minute
])


def fetch_stock_data(selected_stock, start_date, end_date):
    end_date_adjusted = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    query = {"Ticker": selected_stock, "Timestamp": {"$gte": start_date, "$lt": end_date_adjusted}}
    data = list(collection.find(query, {"_id": 0}))
    return pd.DataFrame(data)


def get_top_gainers_losers(start_date, end_date):
    end_date_adjusted = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    results = []

    for stock in STOCKS:
        query = {"Ticker": stock, "Timestamp": {"$gte": start_date, "$lt": end_date_adjusted}}
        data = list(collection.find(query, {"_id": 0}))
        df = pd.DataFrame(data)

        if not df.empty and len(df) >= 2:
            first_price = df.iloc[0]['Close']
            last_price = df.iloc[-1]['Close']
            percentage_change = ((last_price - first_price) / first_price) * 100

            results.append({'Ticker': stock, 'First_Price': first_price, 'Last_Price': last_price, 'Percentage_Change': percentage_change})

    result_df = pd.DataFrame(results)
    if result_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    result_df = result_df.sort_values(by='Percentage_Change', ascending=False)
    top_gainers = result_df.head(10)
    top_losers = result_df.tail(10).iloc[::-1]
    return top_gainers, top_losers


@app.callback(
    Output('tabs-content', 'children'),
    [Input("tabs", "value"),
     Input("stock-dropdown", "value"),
     Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_tab(tab, selected_stock, start_date, end_date):
    df = fetch_stock_data(selected_stock, start_date, end_date)

    if tab == 'tab1':
        fig = go.Figure()
        if not df.empty:
            fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["Close"], mode="lines", name="Close Price"))
        fig.update_layout(title="Price Analysis", xaxis_title="Time", yaxis_title="Price")
        return dcc.Graph(figure=fig)

    elif tab == 'tab2':
        fig = go.Figure()
        if not df.empty:
            df['SMA'] = df['Close'].rolling(window=20).mean()
            df['EMA'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['MACD'] = df['EMA'] - df['Close'].ewm(span=9, adjust=False).mean()
            fig.add_trace(go.Scatter(x=df["Timestamp"], y=df['SMA'], mode="lines", name="SMA"))
            fig.add_trace(go.Scatter(x=df["Timestamp"], y=df['EMA'], mode="lines", name="EMA"))
            fig.add_trace(go.Scatter(x=df["Timestamp"], y=df['MACD'], mode="lines", name="MACD"))
        fig.update_layout(title="Technical Indicators", xaxis_title="Time", yaxis_title="Value")
        return dcc.Graph(figure=fig)


    elif tab == 'tab3':

        top_gainers, top_losers = get_top_gainers_losers(start_date, end_date)

        if top_gainers.empty or top_losers.empty:
            return html.H3(f"No sufficient data available for the period {start_date} to {end_date}")

        gainers_table = html.Table([

            html.Thead(html.Tr([html.Th(col) for col in top_gainers.columns])),

            html.Tbody([

                html.Tr([html.Td(row[col]) for col in top_gainers.columns]) for _, row in top_gainers.iterrows()

            ])

        ], style={'width': '100%', 'border': '1px solid black', 'textAlign': 'center', 'borderCollapse': 'collapse'})

        losers_table = html.Table([

            html.Thead(html.Tr([html.Th(col) for col in top_losers.columns])),

            html.Tbody([

                html.Tr([html.Td(row[col]) for col in top_losers.columns]) for _, row in top_losers.iterrows()

            ])

        ], style={'width': '100%', 'border': '1px solid black', 'textAlign': 'center', 'borderCollapse': 'collapse'})

        return html.Div([

            dcc.Graph(figure=px.bar(top_gainers, x='Ticker', y='Percentage_Change', text='Percentage_Change',

                                    title=f'Top 10 Gainers ({start_date} to {end_date})',

                                    color='Percentage_Change', color_continuous_scale='Greens')),

            gainers_table,

            dcc.Graph(figure=px.bar(top_losers, x='Ticker', y='Percentage_Change', text='Percentage_Change',

                                    title=f'Top 10 Losers ({start_date} to {end_date})',

                                    color='Percentage_Change', color_continuous_scale='Reds_r')),

            losers_table

        ])


    elif tab == 'tab4':  # Volume Analysis

        if df.empty:
            return html.H3("No data available for Volume Analysis")

        fig = go.Figure()

        fig.add_trace(go.Bar(x=df["Timestamp"], y=df["Volume"], name="Volume", marker_color='#8B0000'))

        fig.update_layout(title="Volume Analysis", xaxis_title="Time", yaxis_title="Volume")

        volume_table = html.Table([

            html.Thead(html.Tr([html.Th("Date"), html.Th("Volume")])),

            html.Tbody([

                html.Tr([html.Td(row["Timestamp"]), html.Td(row["Volume"])]) for _, row in df.iterrows()

            ])

        ], style={'width': '100%', 'border': '1px solid black', 'textAlign': 'center', 'borderCollapse': 'collapse'})

        return html.Div([

            dcc.Graph(figure=fig),

            html.H3("Volume Data Table"),

            volume_table

        ])


    elif tab == 'tab5':  # Moving Averages
        if df.empty:
            return html.H3("No data available for Moving Averages")

        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["Close"], mode="lines", name="Close Price", line=dict(color='black')))
        fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["SMA_50"], mode="lines", name="SMA 50", line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["SMA_200"], mode="lines", name="SMA 200", line=dict(color='red')))
        fig.update_layout(title="Moving Averages", xaxis_title="Time", yaxis_title="Price")

        return dcc.Graph(figure=fig)

    return html.Div()


if __name__ == "__main__":
    app.run(debug=True)
