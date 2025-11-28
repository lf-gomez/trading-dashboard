from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

from dotenv import load_dotenv

from client import BinanceTestClient
from models import AccountInfo, OrderRequest

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("BINANCE_API_KEY", "key")
api_secret = os.getenv("BINANCE_API_SECRET", "secret")
client = BinanceTestClient(api_key, api_secret)


@app.get("/api/health")
async def health():
    return {"message": "OK"}


@app.get("/api/account")
async def get_account() -> AccountInfo:
    """
    Get Binance account information
    """
    try:
        account = client.get_account_info()
        return account
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/price")
async def get_price(symbol: str):
    """
    Get price of a symbol
    """
    try:
        price = client.get_symbol_price(symbol=symbol)
        return price
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/price-history")
async def get_price(symbol: str, interval: str = '1h'):
    """
    Get price of a symbol
    """
    try:
        price = client.get_symbol_price_history(symbol=symbol, interval=interval)
        return price
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/order")
async def create_order(order: OrderRequest):
    """
    Create a Binance order
    """
    try:
        order = client.place_order(**order.dict())
        return order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
