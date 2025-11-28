import hashlib
import hmac
from typing import List

import pandas as pd
import requests
import time
from models import AccountInfo, AssetBalance, Order, PriceInfo, CandleInfo

from urllib.parse import urlencode


class BinanceTestClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = 'https://testnet.binance.vision/api'

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _execute_request(self, endpoint: str, params: dict, method: str = 'GET'):
        timestamp = int(time.time() * 1000)
        params['timestamp'] = timestamp

        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        params['signature'] = signature

        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        if method == 'GET':
            return requests.get(f"{self.base_url}{endpoint}", params=params, headers=headers)

        return requests.post(f"{self.base_url}{endpoint}", params=params, headers=headers)

    def get_symbol_price(self, symbol='BTCUSDT') -> PriceInfo:
        endpoint = '/v3/ticker/price'
        params = {
            'symbol': symbol
        }
        response = requests.get(f"{self.base_url}{endpoint}", params=params).json()
        return PriceInfo.parse_obj(response)

    def get_symbol_price_history(self, symbol='BTCUSDT', interval: str = '1d', limit: int = 500) -> List[CandleInfo]:
        endpoint = '/v3/klines'

        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }

        res = requests.get(f"{self.base_url}{endpoint}", params=params)
        data = res.json()

        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])

        numeric_columns = ['open', 'high', 'low', 'close', 'volume',
                           'quote_asset_volume', 'taker_buy_base_asset_volume',
                           'taker_buy_quote_asset_volume']

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])

        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms').astype('str')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms').astype('str')
        res_dict = df.to_dict(orient='records')
        return [CandleInfo.parse_obj(price) for price in res_dict]

    def get_account_info(self) -> AccountInfo:
        endpoint = '/v3/account'
        res = self._execute_request(endpoint, {}).json()
        btc_balance = list(filter(lambda balance: balance['asset'] == 'BTC', res['balances']))[0]
        usdt_balance = list(filter(lambda balance: balance['asset'] == 'USDT', res['balances']))[0]
        eth_balance = list(filter(lambda balance: balance['asset'] == 'ETH', res['balances']))[0]
        account_info = AccountInfo(uid=res["uid"],
                                   account_type=res["accountType"],
                                   btc_balance=AssetBalance(asset=btc_balance["asset"], balance=btc_balance['free']),
                                   eth_balance=AssetBalance(asset=eth_balance["asset"], balance=eth_balance['free']),
                                   usdt_balance=AssetBalance(asset=usdt_balance['asset'], balance=usdt_balance['free']))
        print(res)
        return account_info

    def place_order(self, symbol='BTCUSDT', side='BUY', order_type='MARKET', quantity=0.001, test=True) -> Order | dict:
        endpoint = '/v3/order'
        if test:
            endpoint += '/test'

        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
        }

        if order_type == 'LIMIT':
            current_price = float(self.get_symbol_price(symbol).price)
            # Add any markup you want here...
            price_modifier = 1.01 if side == 'BUY' else 0.99
            params['price'] = round(current_price * price_modifier, 2)
            params['timeInForce'] = 'GTC'  # Good Till Canceled

        res = self._execute_request(endpoint, params, method='POST').json()
        if test:
            return {}
        return Order.parse_obj(res)
