import os
import asyncio
import sys
import logging
import time
import csv
import threading
from json import JSONDecodeError
from http import HTTPStatus
from logging.handlers import RotatingFileHandler
from typing import List, Literal, TypedDict, Any, Optional

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.error import Forbidden, NetworkError


from custom_exceptions import (
    EmptyError,
    FailedJSONDecodeError,
    FailedRequestError,
    FailedStatusError,
    TelegramMessageError,
)

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler("parser.log", maxBytes=5000000, backupCount=5)
# handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
# handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# logger.addHandler(handler)

URL: str = "https://rooms.vestide.nl"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", 0)
TG_RATE_LIMIT_TIME: int = 5
RETRY_TIME: int = 600
TELEGRAM_POLLING: int = 5

MESSAGE_TEMPLATE: str = """
<b>%s</b> 
%s

Total Price: <b>%s</b> 
"""


class Accomodation(TypedDict):
    id: str
    straatnaamEnHuisnummer: str
    latitude: float
    longitude: float
    advertentietitel: float
    fotoURI: str
    plaatsnaam: Literal["Eindhoven"]
    postcode: str
    totaleHuur: str
    woonoppervlakte: float


async def send_message(bot: Bot, message: str, photo_url: str, link: str):
    try:
        logger.info(f"Бот отправляет сообщение")

        inline_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Apply", url=link)]]
        )

        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=photo_url,
            caption=message,
            reply_markup=inline_keyboard,
            parse_mode="html",
        )
    except Exception as error:
        raise TelegramMessageError(f"Ошибка отправки сообщения: {error}")


def get_api_answer():
    try:
        ENDPOINT: str = URL + "/api/accommodation/getlivingspaces/?Skip=0&Take=999"
        res = requests.get(ENDPOINT)
    except RequestException as error:
        raise FailedRequestError(f"Ошибка запроса к API: {error}")

    if res.status_code != HTTPStatus.OK:
        raise FailedStatusError(f"Ошибка запроса к API: {res.status_code}")

    try:
        return res.json()
    except JSONDecodeError as error:
        raise FailedJSONDecodeError(f"Ошибка декодирования ответа: {error}")


def check_response(response: Any) -> List[Accomodation]:
    if not response:
        raise EmptyError("Ответ пустой")

    if not isinstance(response, list):
        raise TypeError("Ответ не является массивом")

    return response


def apply_link(id: str):
    return URL + "/en/find-room/detail-accommodation/?detailId=%s" % id


def check_tokens():
    return all((TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


async def echo(bot: Bot, update_id: Optional[int]) -> Optional[int]:
    """Echo the message the user sent."""
    # Request updates after the last update_id
    updates = await bot.get_updates(
        offset=update_id, timeout=10, allowed_updates=Update.ALL_TYPES
    )
    for update in updates:
        next_update_id = update.update_id + 1

        # your bot can receive updates without messages
        # and not all messages contain text
        if update.message and update.message.text:
            # Reply to the message
            logger.info("Found message %s!", update.message.text)
            await update.message.reply_text(update.message.text)
        return next_update_id
    return update_id


async def run_bot(bot: Bot):
    try:
        update_id = (await bot.get_updates())[0].update_id
    except IndexError:
        update_id = None

    logger.info("listening for new messages...")
    while True:
        try:
            update_id = await echo(bot, update_id)
        except NetworkError:
            await asyncio.sleep(TELEGRAM_POLLING)
        except Forbidden:
            # The user has removed or blocked the bot.
            if update_id is not None:
                update_id += 1


async def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical("Отсутствует обязательная переменная окружения")
        sys.exit("Программа принудительно остановлена.")

    been = set()
    with open("accomodations.csv", newline="", mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            been.add(row["id"])

    async with Bot(token=TELEGRAM_TOKEN) as bot:
        x = threading.Thread(target=asyncio.run, args=(run_bot(bot),))
        x.start()

        with open("accomodations.csv", newline="", mode="a+") as csvfile:
            fieldnames = ["id"]
            writer = csv.DictWriter(csvfile, fieldnames)

            while True:
                try:
                    res = get_api_answer()

                    accomodations = check_response(res)
                    new = []
                    for acc in accomodations:
                        if acc["id"] not in been:
                            message: str = MESSAGE_TEMPLATE % (
                                acc["straatnaamEnHuisnummer"],
                                acc["advertentietitel"],
                                acc["totaleHuur"],
                            )
                            await send_message(
                                bot, message, acc["fotoURI"][2:], apply_link(acc["id"])
                            )

                            been.add(acc["id"])
                            writer.writerow({"id": acc["id"]})
                            time.sleep(TG_RATE_LIMIT_TIME)
                            new.append(acc["id"])
                    if new:
                        logger.debug("Новых домов нет")
                    else:
                        logger.debug(f"Нашел {len(new)} новых дома: {new}")
                except Exception as error:
                    logger.error(f"Сбой в работе программы: {error}")
                finally:
                    await asyncio.sleep(RETRY_TIME)


if __name__ == "__main__":
    asyncio.run(main())
