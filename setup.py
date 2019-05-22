import os
import sys

from setuptools import setup

if sys.version_info < (3, 5, 3):
    raise RuntimeError("aio-telegram-bot requires Python 3.5.3+")


with open(os.path.join(os.path.dirname(__file__), "aiotelegrambot", "__init__.py")) as f:
    for line in f:
        if line.startswith("__version__ ="):
            _, _, version = line.partition("=")
            VERSION = version.strip(" \n'\"")
            break
    else:
        raise RuntimeError("Unable to read the version from aiotelegrambot/__init__.py")


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    readme = f.read()


setup(
    name="aio-telegram-bot",
    version=VERSION,
    author="Valery Vishnevskiy",
    author_email="v.v.vishnevskiy@gmail.com",
    url="https://github.com/v-v-vishnevskiy/aio-telegram-bot",
    project_urls={
        "CI: Travis": "https://travis-ci.org/v-v-vishnevskiy/aio-telegram-bot",
        "Coverage: codecov": "https://codecov.io/gh/v-v-vishnevskiy/aio-telegram-bot",
        "GitHub: repo": "https://github.com/v-v-vishnevskiy/aio-telegram-bot",
    },
    description="An asynchronous framework for building your own Telegram Bot",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    license="MIT",
    keywords=["aio", "async", "asyncio", "telegram", "bot"],
    packages=["aiotelegrambot"],
    provides=["aiotelegrambot"],
    python_requires=">=3.5.3",
    install_requires=["aiohttp==3.5.4", "aiojobs==0.2.2"],
)
