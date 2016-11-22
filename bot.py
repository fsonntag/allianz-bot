# coding=utf-8
import json
import logging
import random
import base64
import itertools

import requests
import telegram
from pydub import AudioSegment
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

import texts
from microsoft_apis import search_images
from google_apis import voice_recognize

ALLIANZ_LOGO_URL = "http://www.versicherung-2.de/wp-content/uploads/2010/04/allianz_logo.png"

with open("keys.json") as inf:
    keys = json.load(inf)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

updater = Updater(token=keys["telegram"])
bot = telegram.Bot(token=keys["telegram"])

states = {}

dispatcher = updater.dispatcher


def shorten_link(url):
    token = keys["linkShorten"]
    response = requests.post("https://www.googleapis.com/urlshortener/v1/url?key=" + token, json={"longUrl": url})
    return response.json()["id"]


continentsToCountries = {}
continentCodesToNames = {}

with open("insurances.json", "r") as inf1:
    insurance_infos = json.load(inf1)
    concrete_insurances = {}
    for type in insurance_infos['types'].values():
        for category in type.values():
            concrete_insurances.update(category['infos'].items())


def start(bot, update):
    send_image(bot, chat_id=update.message.chat_id, image_url=ALLIANZ_LOGO_URL, text="Hey, I'm Allianzer. What can I tell you about us?")





def find_insurance_in_text(chat_id, message):
    candidates = list(itertools.chain.from_iterable(
        [candidate.split() for candidate in insurance_infos['types']['personal']['car']['infos'].keys()]
    ))
    candidates = [candidate for candidate in candidates if candidate in message]
    if not candidates:
        candidate = states[chat_id]["last_insurance"]
    else:
        candidate = candidates[0]

    states[chat_id]["last_insurance"] = candidate
    return candidate


def resolve_command(chat_id, message):
    message = message.strip().lower()

    if "quote" in message:
        return "quote", find_insurance_in_text(chat_id, message)

    if "extended" in message:
        return "extended", find_insurance_in_text(chat_id, message)

    if "website" in message or "url" in message:
        return "website", find_insurance_in_text(chat_id, message)

    if "comprehensive" in message:
        return "car_detail", "comprehensive"

    if "third" in message or "party" in message:
        return "car_detail", "party"

    if "life" in message and "cover" in message:
        return "life_detail", "cover"

    if "critical" in message or "illness" in message:
        return "life_detail", "illness"

    if "content" in message:
        return "home_detail", "content"

    if "building" in message:
        return "home_detail", "building"

    if "available" in message or "offer" in message:
        return "available", []

    if "car" in message:
        return "car", []

    if "home" in message:
        return "home", []

    if "life" in message:
        return "life", []

    if message == "thanks":
        return "bye", []


def speech_handler(bot, update):
    file_id = update.message.voice.file_id
    chat_id = update.message.chat_id
    newFile = bot.getFile(file_id)
    newFile.download('voice%s.ogg' % chat_id)
    ogg_file = AudioSegment.from_ogg('voice%s.ogg' % chat_id)
    ogg_file.export("voice%s.flac" % chat_id, format="flac")


    with open("voice%s.flac" % chat_id, 'rb') as speech:
        # Base64 encode the binary audio file for inclusion in the JSON
        # request.
        speech_content = base64.b64encode(speech.read())

    body = {
        'config': {
        #     # There are a bunch of config options you can specify. See
        #     # https://goo.gl/KPZn97 for the full list.
            'encoding': 'FLAC',  # raw 16-bit signed LE samples
            'sampleRate': 48000,  # 16 khz
        #     # See https://goo.gl/A9KJ1A for a list of supported languages.
            'languageCode': 'en-US',  # a BCP-47 language tag
        },
        'audio': {
            'content': speech_content.decode('UTF-8')
        }
    }

    update.message.text = voice_recognize(body)
    language_command_handler(bot, update)



def language_command_handler(bot, update):
    chat_id = update.message.chat_id
    text = update.message.text
    try:
        command, args = resolve_command(chat_id, text)
        if command == "car":
            query_car(bot, chat_id)

        if command == "home":
            query_home(bot, chat_id)

        if command == "life":
            query_life(bot, chat_id)

        if command == "extended":
            show_extended(bot, chat_id, args)

        elif command == "car_detail":
            query_car_detail(bot, chat_id, args)

        elif command == "home_detail":
            query_home_detail(bot, chat_id, args)

        elif command == "life_detail":
            query_life_detail(bot, chat_id, args)

        elif command == "party":
            query_images(bot, chat_id, args)

        elif command == "quote":
            quote_insurance(bot, chat_id, args)

        elif command == "website":
            show_info_url(bot, chat_id, args)

        elif command == "available":
            show_available(bot, chat_id)

        elif command == "bye":
            say_bye(bot, chat_id)
    except Exception as e:
        print(e)
        dont_know(bot, chat_id)


def say_bye(bot, chat_id):
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.bye))
    # states[chat_id] TODO reset?


def show_extended(bot, chat_id, insurance):
    detailed_info = concrete_insurances[insurance]
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.extended_detailed_insurance)(detailed_info['name']))
    for info in detailed_info['extended']:
        bot.sendMessage(chat_id=chat_id, text=info)


def quote_insurance(bot, chat_id, insurance):
    quote_url = concrete_insurances[insurance]['quoteUrl']
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.quote)(shorten_link(quote_url)))

def show_info_url(bot, chat_id, insurance):
    url = concrete_insurances[insurance]['url']
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.quote)(shorten_link(url)))

def show_available(bot, chat_id):
    insurance_names = [info['name'] for info in insurance_infos['types']['personal'].values()]
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.available))
    for name in insurance_names:
        bot.sendMessage(chat_id=chat_id, text=name)

def query_car(bot, chat_id):
    options = [insurance['name'] for insurance in insurance_infos['types']['personal']['car']['infos'].values()]

    text = random.choice(texts.car)
    send_image(bot, chat_id, image_url=insurance_infos['types']['personal']['car']['image'], text=text)

    for option in options:
        bot.sendMessage(chat_id=chat_id, text=option)
    states[chat_id] = {"last_action": "car", "depth": "general"}

def query_home(bot, chat_id):
    options = [insurance['name'] for insurance in insurance_infos['types']['personal']['home']['infos'].values()]

    text = random.choice(texts.car)
    send_image(bot, chat_id, image_url=insurance_infos['types']['personal']['life']['image'], text=text)

    for option in options:
        bot.sendMessage(chat_id=chat_id, text=option)
    states[chat_id] = {"last_action": "home", "depth": "general"}

def query_life(bot, chat_id):
    options = [insurance['name'] for insurance in insurance_infos['types']['personal']['life']['infos'].values()]

    text = random.choice(texts.car)
    send_image(bot, chat_id, image_url=insurance_infos['types']['personal']['life']['image'], text=text)

    for option in options:
        bot.sendMessage(chat_id=chat_id, text=option)
    states[chat_id] = {"last_action": "life", "depth": "general"}


def query_car_detail(bot, chat_id, type):
    detailed_info = insurance_infos['types']['personal']['car']['infos'][type]
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.detailed_insurance)(detailed_info['name']))
    for info in detailed_info['infos']:
        bot.sendMessage(chat_id=chat_id, text=info)
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.offer_extended))
    states[chat_id] = {"last_action": "car", "depth": "detail", "last_insurance": type}

def query_home_detail(bot, chat_id, type):
    detailed_info = insurance_infos['types']['personal']['home']['infos'][type]
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.detailed_insurance)(detailed_info['name']))
    for info in detailed_info['infos']:
        bot.sendMessage(chat_id=chat_id, text=info)
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.offer_extended))
    states[chat_id] = {"last_action": "home", "depth": "detail", "last_insurance": type}

def query_life_detail(bot, chat_id, type):
    detailed_info = insurance_infos['types']['personal']['life']['infos'][type]
    bot.sendMessage(chat_id=chat_id, text=random.choice(texts.detailed_insurance)(detailed_info['name']))
    for info in detailed_info['infos']:
        bot.sendMessage(chat_id=chat_id, text=info)
    states[chat_id] = {"last_action": "life", "depth": "detail", "last_insurance": type}


def query_images(bot, chat_id, city):
    urls = search_images(city + " photo")
    idxs = list(range(len(urls)))
    random.shuffle(idxs)
    bot.sendMessage(chat_id=chat_id, text="Here are some pictures of %s!" % city.capitalize())
    for idx in idxs[:min(len(idxs), int(random.random() * 9) + 1)]:
        bot.sendPhoto(chat_id=chat_id, photo=urls[idx])


def dont_know(bot, chat_id):
    bot.sendMessage(chat_id=chat_id, text="Sorry, I didn't understand that!")


# send_image(bot, update.message.chat_id, "https://i.imgur.com/emxhXFm.jpg", u"was für 1 hackathon")
def send_image(bot, chat_id, image_url, text=None):
    bot.sendPhoto(chat_id=chat_id, photo=image_url, caption=text)


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler([Filters.text], language_command_handler)
dispatcher.add_handler(echo_handler)

talk_handler = MessageHandler([Filters.voice], speech_handler)
dispatcher.add_handler(talk_handler)

# MUST BE LAST
unknown_handler = MessageHandler([Filters.command], unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()