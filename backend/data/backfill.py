from kite import connection
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
import time

logging.basicConfig(level=logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    kite = connection()
    if kite is None:
        print("Failed to connect to Kite. Exiting.")
        return

    while True:
        try:
            instruments(kite)
            # backfill(kite, exchange="nse", period=7, interval="15minute", silent=True)
            backfill(kite, exchange="nfo", period=7, interval="15minute", silent=True)
            wait_until_next_15min()
        except Exception as e:
            print(f"Error during backfill: {e}")
            break

    return


def backfill(kite, exchange='nse', period=90, interval="15minute", silent=False):

    start = datetime.now()
    instrument_list = pd.read_csv(f"instruments/instruments-{exchange}.csv")
    instrument_list.sort_values(by="tradingsymbol", inplace=True)
    instrument_list.reset_index(drop=True, inplace=True)

    expiry_dates = pd.read_csv("instruments/expiries.csv")
    expiry_dates.sort_values(by="expiry", inplace=True)
    expiry_dates["expiry"] = pd.to_datetime(expiry_dates["expiry"])
    current_expiry = expiry_dates[expiry_dates["expiry"] >= pd.to_datetime(datetime.now().date())].iloc[0]["expiry"]
    previous_expiry = expiry_dates[expiry_dates["expiry"] < pd.to_datetime(datetime.now().date())].iloc[-1]["expiry"]

    if exchange == 'nfo':
        print(f"Current expiry: {current_expiry}, Previous expiry: {previous_expiry}")

    print(f"Starting backfill for {len(instrument_list)} instruments...")
    req_start = time.time()
    request_count = 0
    for index, instrument in instrument_list.iterrows():
        try:
            from_date = datetime.now().date() - timedelta(days=period if period != 1 else 0)
            if exchange == 'nfo':
                from_date = previous_expiry + timedelta(days=1)
            to_date = datetime.now().date()


            data = kite.historical_data(
                instrument["instrument_token"],
                from_date=from_date,
                to_date=to_date,
                interval=interval,
            )
            request_count += 1

            if exchange == 'nse':
                file_path = f"nse/15m/{instrument['tradingsymbol']}.csv"
            elif exchange == 'nfo':
                file_path = f"nfo/15m/{instrument['name']}-I.csv"

            # Step 1: Read existing data if present
            if os.path.exists(file_path):
                existing_data = pd.read_csv(file_path)
                if 'date' in existing_data.columns:
                    existing_data['date'] = pd.to_datetime(
                        existing_data['date'])
            else:
                existing_data = pd.DataFrame()

            # Step 2: Prepare new data
            data = pd.DataFrame(data)
            data['date'] = pd.to_datetime(data['date'], utc=True).dt.tz_convert(
                'Asia/Kolkata').dt.tz_localize(None)

            # Step 3: Combine and deduplicate
            if not existing_data.empty:
                df = pd.concat([existing_data, data], ignore_index=True)
            else:
                df = data

            df = df.drop_duplicates(subset=['date'], keep='last')

            df.to_csv(file_path, index=False)

            if not silent:
                print(
                    f"Data for {instrument['tradingsymbol']} downloaded successfully. {from_date} to {to_date}")

        except Exception as e:
            print(
                f"Error downloading data for {instrument['tradingsymbol']}: {e}")

    req_end = time.time()
    print(f"[{request_count}] Request time: {req_end - req_start:.2f}s Rate: {request_count / (req_end - req_start):.2f} req/s")

    endtime = datetime.now()
    print("Backfill completed. Total time taken: ",
          endtime - start)
    return


def instruments(kite):
    # nfo
    expiry_dates = pd.read_csv("instruments/expiries.csv")
    expiry_dates["expiry"] = pd.to_datetime(expiry_dates["expiry"])
    expiry_dates = expiry_dates[expiry_dates["expiry"] >= pd.to_datetime(datetime.now().date())]
    expiry_date = expiry_dates["expiry"].min()
    print(expiry_date)

    instrument_data = kite.instruments(exchange="NFO")
    instrument_df = pd.DataFrame(instrument_data)

    nfo = instrument_df.copy()
    nfo = nfo[nfo["segment"] == "NFO-FUT"]
    nfo["expiry"] = pd.to_datetime(nfo["expiry"])
    nfo = nfo[nfo["expiry"]
              == pd.to_datetime(expiry_date)]
    name = nfo["name"].unique()
    nfo.to_csv("instruments/instruments-nfo.csv", index=False)

    # nse
    instrument_data = kite.instruments(exchange="NSE")
    instrument_df = pd.DataFrame(instrument_data)

    nse_cm = instrument_df.copy()
    nse_cm = nse_cm[nse_cm["segment"] == "NSE"]
    nse_cm = nse_cm[nse_cm["tradingsymbol"].isin(name)]
    nse_cm.to_csv("instruments/instruments-nse.csv", index=False)


def wait_until_next_15min():
    now = datetime.now()
    next_minute = (now.minute // 15 + 1) * 15
    if next_minute == 60:
        next_run = now.replace(hour=(now.hour + 1) %
                               24, minute=0, second=15, microsecond=0)
    else:
        next_run = now.replace(minute=next_minute, second=15, microsecond=0)

    wait_seconds = int((next_run - now).total_seconds())

    print(f"Next run scheduled at {next_run.strftime('%H:%M:%S')}")

    try:
        for remaining in range(wait_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer = f"\r⏳ Sleeping... {mins:02d}m {secs:02d}s remaining"
            print(timer, end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⛔️ Interrupted by user.")
        exit(0)

    print("\r✅ Woke up for next run!                      ", end="\n")


if __name__ == "__main__":
    main()
