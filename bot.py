import os
import time
import requests
from datetime import datetime

# =========================================================
# SETTINGS FROM RENDER ENVIRONMENT VARIABLES
# =========================================================

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD"
]

TIMEFRAME = "5min"
OUTPUT_SIZE = 100
RSI_PERIOD = 14

RR = 2.0
PROTECT_R = 0.5

CHECK_EVERY = 300

LOOKBACK = 40
BASE_ATR_MAX = 1.5
MOVE_ATR = 0.8


# =========================================================
# CHECK SETTINGS
# =========================================================

if not TWELVE_DATA_API_KEY:
    print("ERROR: TWELVE_DATA_API_KEY is missing.")

if not TELEGRAM_BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN is missing.")

if not TELEGRAM_CHAT_ID:
    print("ERROR: TELEGRAM_CHAT_ID is missing.")


# =========================================================
# TELEGRAM
# =========================================================

def send_telegram(message):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram settings are missing.")
        return False

    try:

        url = (
            "https://api.telegram.org/bot"
            + TELEGRAM_BOT_TOKEN
            + "/sendMessage"
        )

        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }

        response = requests.post(
            url,
            data=data,
            timeout=20
        )

        result = response.json()

        if result.get("ok"):
            print("Telegram: message sent.")
            return True

        print(
            "Telegram error:",
            result.get("description", "Unknown error")
        )

        return False

    except Exception as e:

        print(
            "Telegram network error:",
            e
        )

        return False


# =========================================================
# GET MARKET DATA
# =========================================================

def get_data(pair):

    try:

        url = "https://api.twelvedata.com/time_series"

        params = {
            "symbol": pair,
            "interval": TIMEFRAME,
            "outputsize": OUTPUT_SIZE,
            "timezone": "UTC",
            "apikey": TWELVE_DATA_API_KEY
        }

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        data = response.json()

        if "values" not in data:

            print(
                "API ERROR:",
                data.get("message", "Unknown error")
            )

            return None

        candles = data["values"]

        candles.reverse()

        return candles

    except Exception as e:

        print(
            "NETWORK ERROR:",
            e
        )

        return None


# =========================================================
# RSI
# =========================================================

def calculate_rsi(closes, period=14):

    if len(closes) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(closes)):

        change = closes[i] - closes[i - 1]

        if change > 0:

            gains.append(change)
            losses.append(0)

        else:

            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:

        current_rsi = 100

    else:

        rs = avg_gain / avg_loss

        current_rsi = 100 - (
            100 / (1 + rs)
        )

    for i in range(period, len(gains)):

        avg_gain = (
            (avg_gain * (period - 1))
            + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1))
            + losses[i]
        ) / period

        if avg_loss == 0:

            current_rsi = 100

        else:

            rs = avg_gain / avg_loss

            current_rsi = 100 - (
                100 / (1 + rs)
            )

    return current_rsi


# =========================================================
# ATR
# =========================================================

def calculate_atr(candles, period=14):

    if len(candles) < period + 1:
        return None

    ranges = []

    for i in range(1, len(candles)):

        high = float(candles[i]["high"])
        low = float(candles[i]["low"])

        previous_close = float(
            candles[i - 1]["close"]
        )

        true_range = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )

        ranges.append(true_range)

    return sum(ranges[-period:]) / period


# =========================================================
# FIND SUPPLY AND DEMAND
# =========================================================

def find_zones(candles):

    current_atr = calculate_atr(candles)

    if current_atr is None:
        return None, None

    demand = None
    supply = None

    start = max(
        2,
        len(candles) - LOOKBACK
    )

    end = len(candles) - 3

    for i in range(start, end):

        base1 = candles[i]
        base2 = candles[i + 1]

        move1 = candles[i + 2]
        move2 = candles[i + 3]

        base1_high = float(base1["high"])
        base1_low = float(base1["low"])

        base2_high = float(base2["high"])
        base2_low = float(base2["low"])

        base1_range = (
            base1_high - base1_low
        )

        base2_range = (
            base2_high - base2_low
        )

        if base1_range > current_atr * BASE_ATR_MAX:
            continue

        if base2_range > current_atr * BASE_ATR_MAX:
            continue

        zone_low = min(
            base1_low,
            base2_low
        )

        zone_high = max(
            base1_high,
            base2_high
        )

        move1_open = float(move1["open"])
        move1_close = float(move1["close"])

        move2_open = float(move2["open"])
        move2_close = float(move2["close"])


        # DEMAND

        if (
            move1_close > move1_open
            and
            move2_close > move2_open
        ):

            move_size = (
                move2_close - zone_high
            )

            if move_size >= current_atr * MOVE_ATR:

                demand = {
                    "low": zone_low,
                    "high": zone_high
                }


        # SUPPLY

        if (
            move1_close < move1_open
            and
            move2_close < move2_open
        ):

            move_size = (
                zone_low - move2_close
            )

            if move_size >= current_atr * MOVE_ATR:

                supply = {
                    "low": zone_low,
                    "high": zone_high
                }

    return demand, supply


# =========================================================
# SIGNAL
# =========================================================

def get_signal(candles):

    if len(candles) < 30:
        return None

    # Ignore currently forming candle
    closed = candles[:-1]

    closes = [
        float(c["close"])
        for c in closed
    ]

    price = closes[-1]

    current_rsi = calculate_rsi(
        closes,
        RSI_PERIOD
    )

    previous_rsi = calculate_rsi(
        closes[:-1],
        RSI_PERIOD
    )

    if current_rsi is None:
        return None

    if previous_rsi is None:
        return None

    demand, supply = find_zones(closed)


    # =====================================================
    # BUY
    # =====================================================

    if demand is not None:

        zone_low = demand["low"]
        zone_high = demand["high"]

        inside_zone = (
            zone_low <= price <= zone_high
        )

        rsi_confirmed = (
            current_rsi <= 45
            and
            current_rsi > previous_rsi
        )

        if inside_zone and rsi_confirmed:

            entry = price

            risk = entry - zone_low

            if risk <= 0:

                current_atr = calculate_atr(
                    closed
                )

                if current_atr is None:
                    return None

                risk = current_atr * 0.5

            sl = entry - risk

            tp = entry + (
                risk * RR
            )

            protect = entry + (
                risk * PROTECT_R
            )

            return {
                "signal": "BUY",
                "price": price,
                "rsi": current_rsi,
                "previous_rsi": previous_rsi,
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "protect": protect,
                "zone_low": zone_low,
                "zone_high": zone_high
            }


    # =====================================================
    # SELL
    # =====================================================

    if supply is not None:

        zone_low = supply["low"]
        zone_high = supply["high"]

        inside_zone = (
            zone_low <= price <= zone_high
        )

        rsi_confirmed = (
            current_rsi >= 55
            and
            current_rsi < previous_rsi
        )

        if inside_zone and rsi_confirmed:

            entry = price

            risk = zone_high - entry

            if risk <= 0:

                current_atr = calculate_atr(
                    closed
                )

                if current_atr is None:
                    return None

                risk = current_atr * 0.5

            sl = entry + risk

            tp = entry - (
                risk * RR
            )

            protect = entry - (
                risk * PROTECT_R
            )

            return {
                "signal": "SELL",
                "price": price,
                "rsi": current_rsi,
                "previous_rsi": previous_rsi,
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "protect": protect,
                "zone_low": zone_low,
                "zone_high": zone_high
            }


    return {
        "signal": "NONE",
        "price": price,
        "rsi": current_rsi,
        "previous_rsi": previous_rsi,
        "demand": demand,
        "supply": supply
    }


# =========================================================
# FORMAT TELEGRAM SIGNAL
# =========================================================

def make_signal_message(pair, result):

    signal = result["signal"]

    emoji = "🟢" if signal == "BUY" else "🔴"

    message = f"""
{emoji} FOREX SIGNAL

PAIR: {pair}
DIRECTION: {signal}

RSI: {result["rsi"]:.2f}
PREVIOUS RSI: {result["previous_rsi"]:.2f}

ENTRY: {result["entry"]:.5f}
STOP LOSS: {result["sl"]:.5f}
TAKE PROFIT: {result["tp"]:.5f}

PROTECT +0.5R: {result["protect"]:.5f}

SUPPLY/DEMAND ZONE:
{result["zone_low"]:.5f} - {result["zone_high"]:.5f}

RISK/REWARD: 1:2
TIMEFRAME: 5 MINUTES

Signal generated by Supply + Demand + RSI.
"""

    return message.strip()


# =========================================================
# START BOT
# =========================================================

print()
print("========================================")
print(" SUPPLY + DEMAND + RSI SIGNAL BOT")
print("========================================")
print("Timeframe:", TIMEFRAME)
print("RSI:", RSI_PERIOD)
print("Risk/Reward: 1:2")
print("Profit protection: +0.5R")
print("Pairs:", len(PAIRS))
print("========================================")
print()

print("BOT STARTED")
print()


# =========================================================
# TEST TELEGRAM
# =========================================================

send_telegram(
    "🤖 FOREX SIGNAL BOT STARTED\n\n"
    "Supply + Demand + RSI\n"
    "Timeframe: 5 minutes\n"
    "Pairs: 5\n"
    "Risk/Reward: 1:2\n"
    "Profit protection: +0.5R"
)


last_signal = {}


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        print()
        print("========================================")
        print("CHECKING MARKET")
        print(
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
        print("========================================")


        for pair in PAIRS:

            print()
            print("------------------------------")
            print(pair)
            print("------------------------------")

            candles = get_data(pair)

            if candles is None:

                print("No market data.")

                continue


            result = get_signal(candles)

            if result is None:

                print("Not enough data.")

                continue


            signal = result["signal"]


            # =================================================
            # SIGNAL FOUND
            # =================================================

            if signal == "BUY" or signal == "SELL":

                candle_time = candles[-2]["datetime"]

                signal_id = (
                    pair
                    + "_"
                    + candle_time
                    + "_"
                    + signal
                )

                if last_signal.get(pair) == signal_id:

                    print(
                        "Same signal already reported."
                    )

                    continue

                last_signal[pair] = signal_id


                print()
                print("🔥🔥🔥 SIGNAL 🔥🔥🔥")
                print(
                    "PAIR:",
                    pair
                )
                print(
                    "DIRECTION:",
                    signal
                )
                print(
                    "RSI:",
                    round(
                        result["rsi"],
                        2
                    )
                )
                print(
                    "PREVIOUS RSI:",
                    round(
                        result["previous_rsi"],
                        2
                    )
                )
                print(
                    "ENTRY:",
                    round(
                        result["entry"],
                        5
                    )
                )
                print(
                    "STOP LOSS:",
                    round(
                        result["sl"],
                        5
                    )
                )
                print(
                    "TAKE PROFIT:",
                    round(
                        result["tp"],
                        5
                    )
                )
                print(
                    "PROTECT +0.5R:",
                    round(
                        result["protect"],
                        5
                    )
                )
                print(
                    "ZONE:",
                    round(
                        result["zone_low"],
                        5
                    ),
                    "-",
                    round(
                        result["zone_high"],
                        5
                    )
                )
                print("RISK/REWARD: 1:2")
                print("🔥🔥🔥🔥🔥🔥🔥🔥")


                # SEND TELEGRAM

                telegram_message = make_signal_message(
                    pair,
                    result
                )

                send_telegram(
                    telegram_message
                )


            # =================================================
            # NO SIGNAL
            # =================================================

            else:

                print(
                    "Price:",
                    round(
                        result["price"],
                        5
                    )
                )

                print(
                    "RSI:",
                    round(
                        result["rsi"],
                        2
                    )
                )

                print(
                    "Previous RSI:",
                    round(
                        result["previous_rsi"],
                        2
                    )
                )


                if result["demand"] is not None:

                    d = result["demand"]

                    print(
                        "Demand:",
                        round(
                            d["low"],
                            5
                        ),
                        "-",
                        round(
                            d["high"],
                            5
                        )
                    )

                else:

                    print("Demand: NONE")


                if result["supply"] is not None:

                    s = result["supply"]

                    print(
                        "Supply:",
                        round(
                            s["low"],
                            5
                        ),
                        "-",
                        round(
                            s["high"],
                            5
                        )
                    )

                else:

                    print("Supply: NONE")


                print("Signal: NONE")


        print()
        print("Next check in 5 minutes...")
        print()


        time.sleep(CHECK_EVERY)


    except KeyboardInterrupt:

        print()
        print("BOT STOPPED")
        break


    except Exception as e:

        print()
        print(
            "MAIN LOOP ERROR:",
            e
        )

        print(
            "Retrying in 30 seconds..."
        )

        time.sleep(30)
