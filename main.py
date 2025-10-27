import requests
from datetime import datetime

# === Настройки ===
BASESCAN_API_KEY = "UM9IG82FWEQKEG74EAVEIIR96SFQ1KESRN"
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImY1NDVhMTNiLTk0ODctNGM0OS04ZmMxLTFhZmY1OTBkYjNjNCIsIm9yZ0lkIjoiNDU5NzAxIiwidXNlcklkIjoiNDcyOTUwIiwidHlwZUlkIjoiYzYwNmNlZGYtMjNlMC00ZDlmLTk3MDMtNTA4NWEyNTU1YWE2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTI2OTUwMzgsImV4cCI6NDkwODQ1NTAzOH0.JHmymPAlysZfTmOmwhFNGHM1tuMVs7rkf5A5i0CmnLs"

START_DATE = datetime(2025, 4, 23)
END_DATE = datetime.now()

# --- Получить блок по дате ---
def get_block_by_date(dt: datetime, moralis_api_key: str):
    dt_str = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    url = f"https://deep-index.moralis.io/api/v2.2/dateToBlock?chain=base&date={dt_str}"
    headers = {"X-API-Key": moralis_api_key}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["block"]

# --- Подсчёт по одному адресу ---
def process_wallet(address, start_block, end_block):
    url = (
        f"https://api.basescan.org/api"
        f"?module=account&action=txlist"
        f"&address={address}"
        f"&startblock={start_block}"
        f"&endblock={end_block}"
        f"&sort=asc"
        f"&apikey={BASESCAN_API_KEY}"
    )
    resp = requests.get(url)
    try:
        resp.raise_for_status()
        data = resp.json()
        if data["status"] != "1" or "result" not in data:
            return None, None, None, "no_tx"
        total_sent = 0
        total_gas_fee = 0
        for tx in data['result']:
            if tx['from'].lower() == address.lower():
                eth_sent = int(tx['value']) / 1e18
                gas_fee = int(tx['gasUsed']) * int(tx['gasPrice']) / 1e18
                total_sent += eth_sent
                total_gas_fee += gas_fee
        total = total_sent + total_gas_fee
        return total_sent, total_gas_fee, total, "ok"
    except Exception as e:
        return None, None, None, str(e)

# --- Основная логика ---
if __name__ == "__main__":
    # Получаем нужные блоки для всего расчёта
    print("Получаем блоки по дате...")
    start_block = get_block_by_date(START_DATE, MORALIS_API_KEY)
    end_block = get_block_by_date(END_DATE, MORALIS_API_KEY)
    print(f"Период: блоки с {start_block} по {end_block}")

    # Читаем кошельки из файла
    with open("wallets.txt", "r") as f:
        wallets = [line.strip() for line in f if line.strip()]

    # Заголовки для CSV
    with open("result.csv", "w") as res:
        res.write("address,sent_eth,fee_eth,total_eth,status\n")
        for address in wallets:
            print(f"Обработка {address} ...")
            sent, fee, total, status = process_wallet(address, start_block, end_block)
            # Запись строки в csv
            res.write(f"{address},{sent if sent is not None else ''},{fee if fee is not None else ''},{total if total is not None else ''},{status}\n")
            print(f"  >> sent: {sent}, fee: {fee}, total: {total}, status: {status}")

