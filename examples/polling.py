import asyncio
import os

from aiotelegrambot import Bot, Client, Content, Message
from aiotelegrambot.rules import Contains


async def hi(message: Message):
    await message.send_message("Hello!", True)


async def run(bot: Bot):
    await bot.initialize()
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    client = Client(os.environ["TELEGRAM_BOT_TOKEN"])
    bot = Bot(client)
    bot.add_handler(hi, content_type=Content.TEXT, rule=Contains("hi"))

    try:
        loop.run_until_complete(run(bot))
    except KeyboardInterrupt:
        loop.run_until_complete(bot.close())
        loop.run_until_complete(bot.client.close())
    finally:
        loop.close()
