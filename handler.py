import json
import telegram
import os
import logging
import requests
import re
import bs4

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

OK_RESPONSE = {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps('ok')
}
ERROR_RESPONSE = {
    'statusCode': 400,
    'body': json.dumps('Oops, something went wrong!')
}


def thug_out(text):
    params = {"translatetext": text}
    target_url = "http://www.gizoogle.net/textilizer.php"
    resp = requests.post(target_url, data=params)
    soup_input = re.sub("/name=translatetext[^>]*>/", 'name="translatetext" >', resp.text)
    try:
        soup = bs4.BeautifulSoup(soup_input, "html")
        giz = soup.find_all(text=True)
        return giz[38].strip("\r\n")
    except:
        soup = bs4.BeautifulSoup(soup_input, "lxml")
        giz = soup.find_all(text=True)
        return giz[38].strip("\r\n")


def configure_telegram():
    """
    Configures the bot with a Telegram Token.

    Returns a bot instance.
    """

    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        logger.error('The TELEGRAM_TOKEN must be set')
        raise NotImplementedError

    return telegram.Bot(TELEGRAM_TOKEN)


def webhook(event, context):
    """
    Runs the Telegram webhook.
    """

    bot = configure_telegram()
    logger.info('Event: {}'.format(event))

    if event.get('httpMethod') == 'POST' and event.get('body'):
        logger.info('Message received:')
        update = telegram.Update.de_json(json.loads(event.get('body')), bot)
        chat_id = update.message.chat.id
        text = update.message.text

        if text.startswith('/start') or text.startswith('/yo'):
            text = """Yo! Type anything casual after the command /thugout"""

        elif text.startswith("/thugout"):
            text = ''.join(thug_out(text).split("/thugout")).strip()

        bot.sendMessage(chat_id=chat_id, text=text)

        return OK_RESPONSE

    return ERROR_RESPONSE


def set_webhook(event, context):
    """
    Sets the Telegram bot webhook.
    """

    logger.info('Event: {}'.format(event))
    bot = configure_telegram()
    url = 'https://{}/{}/'.format(
        event.get('headers').get('Host'),
        event.get('requestContext').get('stage'),
    )
    webhook = bot.set_webhook(url)

    if webhook:
        return OK_RESPONSE

    return ERROR_RESPONSE
