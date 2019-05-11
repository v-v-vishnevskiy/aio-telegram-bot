from aiotelegrambot.middleware import Middlewares


async def test_no_middlewares():
    result = []
    expected = [0]

    async def handler(message):
        result.append(message)

    m = Middlewares()
    await m(0, handler)

    assert result == expected


async def test_one_middleware():
    result = []
    expected = [-1, 0, 1]

    async def handler(message):
        result.append(message)

    async def mw1(message, handler):
        result.append(-1)
        await handler(message)
        result.append(1)

    m = Middlewares()
    m.append(mw1)
    await m(0, handler)

    assert result == expected


async def test_two_middlewares():
    result = []
    expected = [-1, -2, 0, 2, 1]

    async def handler(message):
        result.append(message)

    async def mw1(message, handler):
        result.append(-1)
        await handler(message)
        result.append(1)

    async def mw2(message, handler):
        result.append(-2)
        await handler(message)
        result.append(2)

    m = Middlewares()
    m.append(mw1)
    m.extend(mw2)
    await m(0, handler)

    assert result == expected


async def test_three_middlewares():
    result = []
    expected = [-1, -2, -3, 0, 3, 2, 1]

    async def handler(message):
        result.append(message)

    async def mw1(message, handler):
        result.append(-1)
        await handler(message)
        result.append(1)

    async def mw2(message, handler):
        result.append(-2)
        await handler(message)
        result.append(2)

    async def mw3(message, handler):
        result.append(-3)
        await handler(message)
        result.append(3)

    m = Middlewares()
    m.append(mw1)
    m.extend(mw2, mw3)
    await m(0, handler)

    assert result == expected
