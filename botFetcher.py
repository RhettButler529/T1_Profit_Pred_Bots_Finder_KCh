import json
from operator import index
import time
import pandas as pd
import queries as qr

from requests import post
from json import JSONDecodeError
from datetime import datetime, timedelta, timezone


class Fetcher():
    
    # PancakePredictionV2 Contract Address
    pred_addr = "0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA"
    headers = {'X-API-KEY': "BQYKms3kVxifi8rVjOeogFN6xmkQQs8e"}
    
    
    def __init__(self, num_days, num_txs, last_bet, num_bots) -> None:
        self.num_days_in_hrs = num_days*24
        self.num_txs = num_txs
        self.last_bet = last_bet
        self.num_bots = num_bots
    
    # Uses python request library to post the query and return back json
    # query: query string
    # variables=None: variables if any
    # return json
    def make_request_graphql(self, query: str, variables=None):
        
        while True:
            try:
                request = post('https://graphql.bitquery.io/',
                                json={'query': query, 'variables': variables if variables else {}}, headers=self.headers)
                # print()
                # print(query)
                # print()
                # print(request.json())
                # print()

                if 'errors' in request.json():
                    print("ERROR!!!!!!!")
                    print(request.json())
                    print("waiting...")
                    time.sleep(10)
                    continue
                
                # if 'errors' in request.json()['data']:
                #     print(request.json())
                #     raise JSONDecodeError
                
                return request.json()
            
            except JSONDecodeError:
                print(request)
                print("waiting...")
                time.sleep(10)
                continue
                            
            except Exception as e:
                print()
                print(str(e))
                print()
                print(query)
                print()
                print(request.json())
                return {}

    # Helper function to get date of required day minus current day
    # num: number of days
    # return a string of date
    def get_n_days_ago(self, n):
        utc_now = datetime.now(tz=timezone.utc)
        n_days_ago = utc_now - timedelta(days=n)
        n_days_ago_str = n_days_ago.strftime('%Y-%m-%d')
        return n_days_ago_str
    
    # Helper function to get date of required hour minus current hour
    # num: number of days
    # return a string of date    
    def get_n_hours_ago(self, n):
        utc_now = datetime.now(tz=timezone.utc)
        n_hours_ago = utc_now - timedelta(hours=n)
        n_hours_ago_str = n_hours_ago.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        return n_hours_ago_str
    
    # returns addresses list
    def get_addresses(self):

        # get sender addresses of transactions of n hours
        # get query
        offset = 0
        # all_trades = []
        self.addresses = set()
        
        while True:
            query = qr.fetch_addresses_query(self.get_n_hours_ago(self.last_bet), self.pred_addr, offset)
            trades = self.make_request_graphql(query)['data']['ethereum']['transactions']
            
            if not trades:
                break
            
            for t in trades:
                self.addresses.add(t['sender']['address'])
            # all_trades.extend(trades)            
            offset += 25000

        # DEBUG
        print(len(self.addresses))

    def get_num_txs(self, addr, methods=None, sender=False):
        num = 0
        offset = 0
        
        while True:
            if methods:
                query = qr.get_txs( self.get_n_hours_ago(self.num_days_in_hrs), 
                                    self.pred_addr, 
                                    addr,
                                    methods,
                                    offset)
                
                txs = self.make_request_graphql(query)['data']['ethereum']['smartContractCalls']
            else:
                query = qr.fetch_tx_query(  self.get_n_hours_ago(self.num_days_in_hrs), 
                                            addr,
                                            offset,
                                            sender)
                
                txs = self.make_request_graphql(query)['data']['ethereum']['transactions']
                
                # print(query)
                # print('/n', txs)
                
                # print("Length of transactions:", num + len(txs))
            if not txs:
                break
            
            offset += 1000
            num += len(txs)
            
        return num

    def set_addresses_details(self):

        self.addresses_dict =   {
                                    "address": [],
                                    "betting_txs": [],
                                    "claim_txs": [],
                                    "total_txs": [],
                                    "success_rate": [],
                                    "ratio_total": [],
                                    "final_balance": [],
                                    "starting_balance": [],
                                    "profit": []
                                }
        
        for k, addr in enumerate(self.addresses):
            
            num_betting_txs = self.get_num_txs(addr, ["betBear", "betBull"])
            num_claim_txs = self.get_num_txs(addr, ["claim"])
            num_total_txs = self.get_num_txs(addr) + self.get_num_txs(addr, sender=True)
            
            if num_betting_txs > self.num_txs:
                self.addresses_dict["address"].append(addr), 
                self.addresses_dict["betting_txs"].append(num_betting_txs)
                self.addresses_dict["claim_txs"].append(num_claim_txs)
                self.addresses_dict["total_txs"].append(num_total_txs)
                self.addresses_dict["success_rate"].append((num_claim_txs / num_betting_txs) * 100)
                self.addresses_dict["ratio_total"].append(((num_betting_txs + num_claim_txs) / num_total_txs) if num_total_txs else 0)
                self.addresses_dict["final_balance"].append(0)
                self.addresses_dict["starting_balance"].append(0)
                self.addresses_dict["profit"].append(0)

            print(k, num_betting_txs > self.num_txs)
            
    def get_balance_amount(self, addr, fin_flag=False):
        query = qr.get_balance_query(   addr,
                                        self.get_n_hours_ago(self.num_days_in_hrs) if fin_flag else None)
        
        # print(query)
        # print(self.make_request_graphql(query)['data']['ethereum']['address'])
        try:
            amount = self.make_request_graphql(query)['data']['ethereum']['address'][0]['balances'][0]['value']
            
            if amount < 0:
                raise Exception
            
            return amount
        except Exception as e:
            return 0 

    def get_transfer_values(self, addr, transfer_in=False):
        
        offset = 0
        amount = 0.0
        to_or_send = "sender" if transfer_in else "to"
        
        while True:
            query = qr.get_transfer_query(  self.get_n_hours_ago(self.num_days_in_hrs),
                                            addr,
                                            self.pred_addr,
                                            offset,
                                            transfer_in)

            transfer_values = self.make_request_graphql(query)['data']['ethereum']['transactions']
            
            if not transfer_values:
                break
            
            for tx in transfer_values:
                if not tx[to_or_send]['smartContract']['contractType']:
                    amount += float(tx['any'])
            
            offset += 1000
        
        return amount
    
    def set_balances(self):
        
        print("Final Total Addresses", len(self.addresses_dict['address']))
        
        for k, addr in enumerate(self.addresses_dict['address']):
        
            # Get starting and final balance
            starting_bal = self.get_balance_amount(addr, True) # Profit of last 24hrs
            final_bal = self.get_balance_amount(addr)
            
            # Get transfer in and out total values
            trans_in_amount = self.get_transfer_values(addr, True)
            trans_out_amount = self.get_transfer_values(addr)
            
            self.addresses_dict['final_balance'][k] = final_bal
            self.addresses_dict['starting_balance'][k] = starting_bal
            self.addresses_dict['profit'][k] = final_bal + trans_out_amount - starting_bal - trans_in_amount
            
            print(k, starting_bal, final_bal, self.get_n_hours_ago(self.num_days_in_hrs))
            
    # Executes the top profitable bots program
    def start(self):
        self.get_addresses()
        self.set_addresses_details()
        self.set_balances()
        
        df = pd.DataFrame(self.addresses_dict, columns=self.addresses_dict.keys())
        df.sort_values(by=['profit'], inplace=True, ascending=False)
        
        if len(df) > self.num_bots:
            df.iloc[:self.num_bots].to_excel("top_bots.xlsx", index=None)
        else:
            df.to_excel("top_bots.xlsx", index=None)


with open("config.json") as fp:
    config = json.load(fp)
    
fetcher = Fetcher(config["analyzing_days"], 
                  config["number_txs"], 
                  config["last_bet_hr"], 
                  config["number_bots"])

fetcher.start()