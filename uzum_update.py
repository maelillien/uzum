#!/usr/bin/env python

# uzum_update.py

import re
import requests
#import lxml.html
import numpy as np
import pandas as pd
from lxml import html

import gspread
from pprint import pprint
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

def get_borsasi_date():
    page = requests.get('https://itb.org.tr/UzumSalonu')
    doc = html.fromstring(page.content)
    date_str = doc.xpath('//h1/text()')[0]
    match = re.search(r'(\d+.\d+.\d+)', date_str)
    matched_date = match.group(1)
    return datetime.strptime(matched_date, "%d.%m.%Y").strftime('%m/%d/%Y')

def get_grape_data():
    page = requests.get('https://itb.org.tr/UzumSalonu')
    #doc = lxml.html.fromstring(html.content)
    doc = html.fromstring(page.content)
    tables = doc.xpath('//table[@class="table"]/tr/td/text()')

    # Extract volumes
    volumes_content = doc.xpath('//table[@class="table"]')[0].xpath('./tr/td/text()')
    volumes = volumes_content[1:3]
    volumes.append('')  # Account TMO

    # Extract prices of interest
    prices_content = doc.xpath('//table[@class="table"]')[1].xpath('./tr/td/text()')
    type = prices_content[::2]
    price = prices_content[1::2]
    d = {'type': type, 'price': price}

    df = pd.DataFrame(d)
    selects = df[-df['type'].str.contains('Small|Med.|Jumbo')]
    selects = selects.iloc[np.r_[2, 5:len(selects)], :]

    # Extract conversion rate
    rates = doc.xpath('//table[@class="table table-dotted"]/tr/td/text()')

    # Assemble into a flat list of data
    row = [volumes, list(selects.price), rates[1:3]]
    flat_row = [item for sublist in row for item in sublist]  # Flatten lists

    return flat_row


def update_gs(row):
    # Initialize
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    # Select the sheet and get the gata
    sheet = client.open('Uzum Borsasi').sheet1
    data = sheet.get_all_records()
    # pprint(data)
    # pprint(len(data))

    # Enter and format new row
    last_row = len(data) + 2
    sheet.insert_row(row, last_row, value_input_option='USER_ENTERED')
    range = 'B{}:V{}'.format(last_row, last_row)
    sheet.format(range, {"horizontalAlignment": "RIGHT"})


if __name__ == "__main__":

    borsasi_date = get_borsasi_date()
    today = datetime.today().strftime('%m/%d/%Y')
    if borsasi_date == today:
        row = get_grape_data()
        row.insert(0, datetime.today().strftime('%m/%d/%Y')) # Add date
        # print(row)
        update_gs(row)
