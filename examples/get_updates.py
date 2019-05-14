import asyncio
import logging
import os

from aiohttp import ClientError, ClientTimeout

from aiotelegrambot import Bot, Client, Content, Handlers, Message
from aiotelegrambot.rules import Contains

logger = logging.getLogger(__name__)
handlers = Handlers()


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


async def run(bot: Bot):
    await bot.initialize()
    while True:
        await asyncio.sleep(1)


async def close(bot: Bot):
    await bot.close()
    await bot.client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    client = MyClient(os.environ["TELEGRAM_BOT_TOKEN"], timeout=ClientTimeout(total=5))
    bot = Bot(client, handlers)

    try:
        loop.run_until_complete(run(bot))
    except KeyboardInterrupt:
        loop.run_until_complete(close(bot))
    finally:
        loop.close()
