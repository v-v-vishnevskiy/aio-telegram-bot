import argparse
import asyncio
import json
import logging
import os
import ssl

from aiohttp import ClientError, ClientTimeout, web
from async_generator import async_generator, yield_

from aiotelegrambot import Bot, Client, Content, Handlers, Message
from aiotelegrambot.rules import Contains

logger = logging.getLogger(__name__)

handlers = Handlers()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
HOST = os.environ["TELEGRAM_BOT_HOST"]
PORT = 8443

parser = argparse.ArgumentParser()
parser.add_argument("files", metavar="N", type=str, nargs="+")
SSL_PUBLIC_KEY, SSL_PRIVATE_KEY = parser.parse_args().files


class MyClient(Client):
    async def request(self, method: str, api: str, **kwargs) -> dict:
        try:
            return await super().request(method, api, **kwargs)
        except asyncio.TimeoutError:
            logger.exception("Timeout")
        except ClientError:
            logger.exception("Can't connect to telegram API")
        except Exception:
            logger.exception("Error")


@handlers.add(content_type=Content.TEXT, rule=Contains("hi"))
async def hi(message: Message):
    await message.send_message("Hello!")


async def webhook_handle(request):
    bot = request.app["bot"]
    data = await request.text()
    await bot.process_update(json.loads(data))
    return web.Response()


@async_generator
async def init_bot(app: web.Application):
    client = MyClient(TOKEN, timeout=ClientTimeout(total=5))
    bot = Bot(client, handlers)
    await bot.initialize(webhook=True)
    await client.set_webhook("https://{}:{}/{}".format(HOST, PORT, TOKEN), certificate=SSL_PUBLIC_KEY)

    app["bot"] = bot

    await yield_()

    await client.delete_webhook()
    await bot.close()
    await bot.client.close()


app = web.Application()
app.router.add_post("/{}".format(TOKEN), webhook_handle)
app.cleanup_ctx.extend([init_bot])

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(SSL_PUBLIC_KEY, SSL_PRIVATE_KEY)

web.run_app(app, host="0.0.0.0", port=PORT, ssl_context=context)
