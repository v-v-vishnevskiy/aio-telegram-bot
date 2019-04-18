from setuptools import setup, find_packages


setup(
    name="aio-telegram-bot",
    version="0.0.1",
    author="Valery Vishnevskiy",
    author_email="v.v.vishnevskiy@gmail.com",
    license="MIT",
    packages=find_packages(),
    install_requires=["aiohttp==3.5.4"],
)
