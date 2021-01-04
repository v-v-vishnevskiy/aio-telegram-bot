import argparse
import json
import os
import ssl

from aiohttp import web

from aiotelegrambot import Bot, Client, Content, Handlers, Message
from aiotelegrambot.rules import Contains

handlers = Handlers()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
HOST = os.environ["TELEGRAM_BOT_HOST"]
PORT = 8443

parser = argparse.ArgumentParser()
parser.add_argument("files", metavar="N", type=str, nargs="+")
SSL_PUBLIC_KEY, SSL_PRIVATE_KEY = parser.parse_args().files


@handlers.add(content_type=Content.TEXT, rule=Contains("hi"))
async def hi(message: Message):
    await message.send_message("Hello!")


async def webhook_handle(request):
    bot = request.app["bot"]
    data = await request.text()
    await bot.process_update(json.loads(data))
    return web.Response()


async def init_bot(app: web.Application):
    bot = Bot(Client(TOKEN), handlers)
    await bot.initialize(webhook=True)
    await bot.client.set_webhook(f"https://{HOST}:{PORT}/{TOKEN}", certificate=SSL_PUBLIC_KEY)

    app["bot"] = bot

    yield

    await bot.client.delete_webhook()
    await bot.close()
    await bot.client.close()


app = web.Application()
app.router.add_post(f"/{TOKEN}", webhook_handle)
app.cleanup_ctx.extend([init_bot])

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(SSL_PUBLIC_KEY, SSL_PRIVATE_KEY)

web.run_app(app, host="0.0.0.0", port=PORT, ssl_context=context)
