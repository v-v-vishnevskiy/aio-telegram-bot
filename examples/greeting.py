import asyncio
import os

from aiotelegrambot import Bot, Client, Content, Handlers, Message

handlers = Handlers()


@handlers.add(content_type=Content.NEW_CHAT_MEMBERS)
async def greeting(msg: Message):
    user = msg.raw["message"]["new_chat_members"][0]
    name = " ".join([user[key] for key in ("first_name", "last_name") if key in user])
    await msg.send_message("Welcome, {}!".format(name))


async def run(bot: Bot):
    await bot.initialize()
    while True:
        await asyncio.sleep(1)


async def close(bot: Bot):
    await bot.close()
    await bot.client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    bot = Bot(Client(os.environ["TELEGRAM_BOT_TOKEN"]), handlers)

    try:
        loop.run_until_complete(run(bot))
    except KeyboardInterrupt:
        loop.run_until_complete(close(bot))
    finally:
        loop.close()
