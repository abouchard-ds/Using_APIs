# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 11:57:25 2021

@author: alexandre.bouchard1
"""
import requests
import pandas as pd
import json
import datetime


bearer_token = "token here"
board_id = "board id here"

proxiez = {"http"  : '0000', 
           "https" : '0000'}

# GET CARDS
url = "https://api.miro.com/v1/boards/" + board_id + "/widgets/?widgetType=card"
headers = {"Authorization": "Bearer " + bearer_token}

response = requests.request("GET", url, headers=headers, proxies=proxiez)

i = json.loads(response.text)

boardcards=pd.DataFrame()
for card in i['data']:
    boardcards = boardcards.append(card, ignore_index=True)

boardcards.to_excel("/destination/mirocards_" + str(datetime.date.today()) + '.xlsx', index=False)

# Delete cards using coordinates
todel = boardcards[boardcards['x'] == -765460.515181842]

todel['Comp_Date'] = datetime.date.today()
todel.to_excel("/destination/cards_deleted_" + str(datetime.date.today()) + '.xlsx', index=False)

dellist = todel['id']

# DELETE PATTERN
# https://api.miro.com/v1/boards/[[BOADRD ID]]/widgets/[[widgetId]]

for cardID in dellist:
    
    url = "https://api.miro.com/v1/boards/" + board_id + "/widgets/" + cardID
    headers = {"Authorization": "Bearer " + bearer_token}
    response = requests.request("DELETE", url, headers=headers, proxies=proxiez)
