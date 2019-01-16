from urllib.parse import quote

import dash
import dash_core_components as dcc
import dash_html_components as html
import flask
import pandas as pd

import functions as fct

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server)

# Get companies exchange and symbol
companies_df = fct.companies_symbol()
report = pd.DataFrame()


# Function to get companies statement
def get_statement(companies, statements):
    statement_df = fct.companies_statement(companies, statements)
    global report
    report = statement_df
    return fct.show_statement(statement_df)


app.layout = html.Div([
    html.H1('Nasdaq Companies Statements Scrape'),
    dcc.Markdown(''' --- '''),
    html.Div([
        html.Div([
            html.Label('Filters:'),
            dcc.Dropdown(id='dropdown-exchange',
                         options=[{'label': exchange, 'value': exchange} for exchange in
                                  companies_df.sort_values(by=['Exchange']).Exchange.unique()],
                         multi=True,
                         placeholder='Exchange'),
            dcc.Dropdown(id='dropdown-company',
                         multi=True,
                         placeholder='Company'),
            dcc.Dropdown(id='dropdown-statement',
                         multi=False,
                         placeholder='Statement')

        ], style={'display': 'inline-block', 'verticalAlign': 'top', 'width': '30%'}),
        html.Div([
            html.Button(id='button-submit',
                        n_clicks=0,
                        children='Scrape!',
                        style={'fontSize': 24, 'marginLeft': '30px', 'margin-top': '20px'}
                        )

        ], style={'display': 'inline-block'}),
        dcc.Markdown(''' --- '''),
        html.Div(id='loading'),
        html.Div(id='loading-completed'),
        html.A(id='download-link'),
        html.Div(
            id="statement-table"
        )
    ])
])


@app.callback(
    dash.dependencies.Output('dropdown-company', 'options'),
    [dash.dependencies.Input('dropdown-exchange', 'value')])
def set_company_options(exchanges):
    if (exchanges is not None) & (exchanges != []):
        return [{'label': row.Symbol.strip(), 'value': row.Symbol.strip()} for index, row in
                companies_df.sort_values(by=['Symbol']).iterrows() if row.Exchange in exchanges]
    else:
        return []


@app.callback(
    dash.dependencies.Output('dropdown-statement', 'options'),
    [dash.dependencies.Input('dropdown-company', 'value'), dash.dependencies.Input('dropdown-exchange', 'value')])
def enable_dropdown_statement(companies, exchanges):
    if (companies is not None) & (companies != []) & (exchanges is not None) & (exchanges != []):
        return [{'label': 'Balance Sheet', 'value': 'balance-sheet'},
                {'label': 'Income Statement', 'value': 'income-statement'},
                {'label': 'Cash Flow', 'value': 'cash-flow'}]
    else:
        return []


@app.callback(
    dash.dependencies.Output('loading', 'children'),
    [dash.dependencies.Input('button-submit', 'n_clicks')],
    [dash.dependencies.State('dropdown-company', 'value'),
     dash.dependencies.State('dropdown-statement', 'value')])
def check_fields(n_clicks, companies, statements):
    if (n_clicks > 0) & ((companies is not None) & (companies != [])) & ((statements is not None) & (statements != [])):
        return html.Div(
            [dcc.Markdown(
                '''Scraping data...''')], id='loading-completed'), html.Div([], id='statement-table')
    elif n_clicks == 0:
        return html.Div([], id='loading-completed'), html.Div([], id='statement-table')


@app.callback(
    dash.dependencies.Output('statement-table', 'children'),
    [dash.dependencies.Input('loading', 'children'),
     dash.dependencies.Input('button-submit', 'n_clicks')],
    [dash.dependencies.State('dropdown-company', 'value'),
     dash.dependencies.State('dropdown-statement', 'value')])
def set_statement_table(loading, n_clicks, companies, statements):
    if (len(loading) > 0) & (n_clicks > 0) & ((companies is not None) & (companies != [])) & (
            (statements is not None) & (statements != [])):
        return get_statement(companies, statements)
    elif (len(loading) == 0) | (n_clicks == 0):
        return html.Div()
    else:
        return html.Div('Please fill in all fields')


@app.callback(
    dash.dependencies.Output('loading-completed', 'children'),
    [dash.dependencies.Input('statement-table', 'children'),
     dash.dependencies.Input('button-submit', 'n_clicks')],
    [dash.dependencies.State('dropdown-company', 'value'),
     dash.dependencies.State('dropdown-statement', 'value')])
def finish_loading(table, n_clicks, companies, statements):
    if (table is not None) & (table != []) & (n_clicks > 0) & (
            (companies is not None) & (companies != [])) & ((statements is not None) & (
            statements != [])):
        return html.Div([dcc.Markdown(
            '''Data scraped.'''),
            html.A(
                'Download Data',
                id='download-link',
                download="report.csv",
                href="data:text/csv;charset=utf-8,%EF%BB%BF" + quote(report.to_csv(index=False, encoding='utf-8')),
                target="_blank"
            )])


if __name__ == '__main__':
    app.run_server(debug=True)
