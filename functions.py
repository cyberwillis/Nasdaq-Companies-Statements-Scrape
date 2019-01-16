import re
from random import randint
from time import sleep
import dash_table_experiments as dt
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup


# Function to get available exchanges
def exchanges_symbol():
    # Main statements
    exchanges_url = 'https://www.nasdaq.com/screening/company-list.aspx'
    exchanges_response = requests.get(exchanges_url)
    exchanges_html = BeautifulSoup(exchanges_response.text, 'html.parser')
    exchanges = [exchange.text for value in exchanges_html.find_all('tbody') \
                 for exchange in value.find_all('a') if exchange is not None and '\n' not in exchange]
    return exchanges


# Function to get available symbols
def companies_symbol():
    # Request initial setting
    companies_df = []
    exchanges = exchanges_symbol()

    # Start exchange loop
    for exchange in exchanges:
        # Get exchange companies html code
        url_exchanges_companies = 'https://www.nasdaq.com/screening/companies-by-industry.aspx?exchange=' + exchange + '&pagesize=50'
        response_companies = requests.get(url_exchanges_companies)
        html_companies = BeautifulSoup(response_companies.text, 'html.parser')

        # Get exchange companies number
        for number in html_companies.find_all('div', id='resultsDisplay'):
            for final in number.find_all('small'):
                sep = str(final.text).find('-') + 1
                companies_number = str(final.text)[sep:].replace('results', '').replace(' ', '').split('of')[-1]

        # Adjust exchange companies html code companies number
        url_exchanges_companies = url_exchanges_companies.replace('50', companies_number)
        response_companies = requests.get(url_exchanges_companies)
        html_companies = BeautifulSoup(response_companies.text, 'html.parser')

        # Build companies main data dataframe
        row = 0
        column = 0
        company_mdata = pd.DataFrame()
        for company in html_companies.find_all('table', id='CompanylistResults'):
            for data in company.find_all('td'):
                company_mdata.loc[row, column] = str(data.text).replace('\n', '').replace('\r', '').replace('\t', '')
                if column == 7:
                    column = 0
                    row += 1
                else:
                    column += 1
        company_df = company_mdata.loc[:, 1:6]
        company_df = company_df.drop([3], axis=1)
        company_df.rename(columns={1: 'Symbol', 2: 'Market_Cap', 4: 'Country', 5: 'IPO_Year', 6: 'Subsector'},
                          inplace=True)
        company_df['Exchange'] = exchange
        companies_df.append(company_df)
    companies_df = pd.concat(companies_df, ignore_index=True)

    # Treat data
    for row in range(len(companies_df)):
        if companies_df.iloc[row, 1] != 'n/a' and type(companies_df.iloc[row, 1]) != float:
            if companies_df.iloc[row, 1].find('M') >= 0:
                companies_df.iloc[row, 1] = float(companies_df.iloc[row, 1].replace('$', '').replace('M', '')) * 1000000
            elif companies_df.iloc[row, 1].find('B') >= 0:
                companies_df.iloc[row, 1] = float(
                    companies_df.iloc[row, 1].replace('$', '').replace('B', '')) * 1000000000
        companies_df.replace('n/a', np.nan, inplace=True)
    companies_df['Symbol'] = companies_df['Symbol'].apply(lambda x: x.strip())
    return companies_df


# Function to get company statement
def companies_statement(companies, statements):
    # Request initial setting
    companies_statement_list = []
    companies_statement = pd.DataFrame()

    for symbol in companies:
        # Get income statement html code
        url_statement_sheet = 'https://www.nasdaq.com/symbol/' + str(symbol).lower() + '/financials?query=' + str(
            statements)
        response_statement_sheet = requests.get(url_statement_sheet)
        html_statement_sheet = BeautifulSoup(response_statement_sheet.text, 'html.parser')

        # Test if exist data
        result = ['There is currently no data for this symbol.' in test.text for test in
                  html_statement_sheet.find_all('div', class_='notTradingIPO')]
        if bool(result) == True:
            continue

        # Pause
        sleep(randint(1, 4))

        # Get income statement data reference
        data = []
        for statement in html_statement_sheet.find_all('div', class_='genTable'):
            for table in html_statement_sheet.find_all('tr'):
                if table.th is not None:
                    data.append(table.th.text)

        # Get income statement data values
        element_list = []
        for statement in html_statement_sheet.find_all('div', class_='genTable'):
            for table in html_statement_sheet.find_all('tr'):
                element = list(filter(None, str(table.text).replace('Trend', '').split('\n')))
                if table.text is not None and len(element) > 1 and any(e in element for e in data):
                    element_list.append(element)

        # Build income statement dataframe
        statement_sheet_df = pd.DataFrame(element_list[1:], columns=element_list[0])
        statement_sheet_df['Symbol'] = symbol
        companies_statement_list.append(statement_sheet_df)

    if len(companies_statement_list) > 0:
        companies_statement = pd.concat(companies_statement_list, ignore_index=True)

        ignore_columns = ['Period Ending:', 'Symbol']
        # Format numeric data
        for column in companies_statement:

            if column not in ignore_columns:
                companies_statement[column] = companies_statement[column].apply(
                    lambda x: float(re.sub('[^A-Za-z0-9]+', '', str(x))) if str(x).find('(') < 0 else float(
                        re.sub('[^A-Za-z0-9]+', '', str(x))) * -1)

        for column in companies_statement.columns:
            if column not in ignore_columns:
                companies_statement[column] = companies_statement[column].map(lambda x: '{:,.0f}'.format(x))

        companies_statement = companies_statement.loc[:,
                              ignore_columns + [column for column in companies_statement.columns if
                                                column not in ignore_columns]]
    else:
        companies_statement = 'No statements.'

    return companies_statement.replace('nan','')


def show_statement(df):
    return dt.DataTable(
        rows=df.to_dict('rows'),


        # optional - sets the order of columns
        columns=df.columns,

        filterable=True,
        sortable=True,
        editable=False,

        id='table-statement'
    )