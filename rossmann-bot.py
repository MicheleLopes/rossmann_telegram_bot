import json
import pandas as pd
import requests
import os

from flask import Flask, request, Response

#constants
TOKEN = '6395263644:AAF_92IJDQPfGe2TYWjlhgMHEKDBBfrf7P8'

#Info abouth the bot
#https://api.telegram.org/bot6395263644:AAF_92IJDQPfGe2TYWjlhgMHEKDBBfrf7P8/getMe

#Get updates
#https://api.telegram.org/bot6395263644:AAF_92IJDQPfGe2TYWjlhgMHEKDBBfrf7P8/getUpdates

#Webhook
#https://api.telegram.org/bot6395263644:AAF_92IJDQPfGe2TYWjlhgMHEKDBBfrf7P8/setWebhook?url=https://79ca835c2cf924.lhr.life

#Send Message
#https://api.telegram.org/bot6395263644:AAF_92IJDQPfGe2TYWjlhgMHEKDBBfrf7P8/sendMessage?chat_id=5698453693&text=Hi, how are you?


def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/'
    url = url + f"sendMessage?chat_id={chat_id}"

    r = requests.post( url, json={'text': text} )
    print('Status Code {}'.format(r.status_code))
    
    return None
    
def load_dataset(store_id):
    # loading test dataset
    df10 = pd.read_csv( 'test.csv' )
    df_store_raw = pd.read_csv('store.csv', low_memory=False)

    # merge test dataset + store
    df_test = pd.merge( df10, df_store_raw, how='left', on='Store' )
    # choose store for prediction
    df_test = df_test[df_test['Store']== store_id]
    
    if not df_test.empty:
        
        # remove closed days
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop( 'Id', axis=1 )

        # convert Dataframe to json
        data = json.dumps( df_test.to_dict( orient='records' ) )
        
    else:
        data = 'error'
        
    return data

def predict(data):

    # API Call

    url = 'https://rossmann-api-oy3p.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json' }
    data = data
    r = requests.post( url, data=data, headers=header )
    print( 'Status Code {}'.format( r.status_code ) )

    d1 = pd.DataFrame( r.json(), columns=r.json()[0].keys() )
    return d1

def parse_message( message ):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
    
    store_id = store_id.replace('/', '')
    
    try:
        store_id = int(store_id)
        
    except ValueError:
        store_id = 'error'
        
    return chat_id, store_id
    
#API Initialize
app = Flask( __name__ )

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = request.get_json()
        
        chat_id, store_id = parse_message(message)
        if store_id != 'error':
            #loading data
            data = load_dataset(store_id)
            if data != 'error':
                #Prediction
                d1 = predict(data)
                #Calculation
                d2 = d1[['store', 'prediction']].groupby('store'
                                            ).sum().reset_index()
                #send message
                msg = 'Store Number {} will sell R${:,.2f} in the next 6 weeks'.format(d2['store'].values[0], d2['prediction'].values[0] ) 
                
                send_message(chat_id, msg)
                return Response('Ok', status=200)
                
            else:
                send_message(chat_id, 'Store Not Availible')
                return Response('Ok', status=200)
            
        else:
            send_message(chat_id, 'This is not a store number, please write a number within the range 1 to 1115')
            return Response('OK', status=200)
    else:
        return Response('OK', status=200)
if __name__ == '__main__':
    port= os.environ.get('PORT', 5000)
    app.run( host='0.0.0.0', port=port )