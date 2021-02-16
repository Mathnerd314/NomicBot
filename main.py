#!/usr/bin/python3

import asyncio
import datetime
import logging
import os
import sqlite3

import discord

import world
from commands import handleCommand

LOGGER_FORMAT = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
logger = logging.getLogger()

file_handler = logging.FileHandler(
    filename="discord-bot.log", encoding="utf-8", mode="w"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(LOGGER_FORMAT))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOGGER_FORMAT))
logger.addHandler(console_handler)


class DiscordExceptionFormatter(logging.Formatter):
    """
    Wraps the exception trace in code blocks
    """

    def formatException(self, ei):
        trace = traceback.format_exception(ei[0], ei[1], tb[2])
        message = ""
        for line in trace:
            message += "```python\n{}```".format(line)
        return message


class DiscordHandler(logging.Handler):
    """
    A handler class which logs to a Discord channel
    """

    def __init__(self, channel):
        super().__init__(self)
        self.channel = channel
        self.setLevel(logging.WARNING)
        self.setFormatter(DiscordExceptionFormatter(LOGGER_FORMAT))

    def emit(self, record):
        """
        Emit a record.
        """
        message = self.format(record)
        asyncio.create_task(channel.send(message))


class GameBot(discord.Client):
    def __init__(self, w):
        super().__init__()
        self.world = w

    async def on_error(self, event_method, *args, **kwargs):
        logger.exception("Ignoring exception in {}", event_method)

    async def on_ready(self):
        logger.info("Bot ready")

    async def on_message(self, message):
        await handleCommand(self.world, message)


w = world.World()
w.entrypoint = __file__
w.datapath = os.path.dirname(__file__)
dbpath = os.path.join(w.datapath, "database.sqlite3")
if os.path.isfile(dbpath):
    w.db = sqlite3.connect(dbpath)
else:
    # first run
    w.db = sqlite3.connect(dbpath)
    w.db.executescript(open(os.path.join(w.datapath, "initial_schema.sql"), "r").read())
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, stdout=PIPE
    ).stdout
    updateSetting(w, "commit", commit)

w.bot = GameBot(w)


async def run():
    try:
        discordToken = getSetting(w, "discordToken")

        await w.bot.login(discordToken)

        channelID = getSetting(w, "logChannel")
        if channelID != None:
            channel = w.bot.get_channel(channelID)
            logger.addHandler(DiscordHandler(channel))

        await w.bot.connect()

    finally:
        if not w.bot.is_closed():
            await w.bot.close()


w.loop = asyncio.get_event_loop()
w.loop.add_signal_handler(signal.SIGINT, lambda: w.loop.stop())
w.loop.add_signal_handler(signal.SIGTERM, lambda: w.loop.stop())
future = asyncio.ensure_future(run(), loop=w.loop)


def stop_loop_on_completion(f):
    return w.loop.stop()


future.add_done_callback(stop_loop_on_completion)
try:
    w.loop.run_forever()
except KeyboardInterrupt:
    log.info("Received signal to terminate bot and event loop.")
finally:
    future.remove_done_callback(stop_loop_on_completion)
    log.info("Cleaning up tasks.")
    discord.client._cleanup_loop(loop)

if not future.cancelled():
    try:
        return future.result()
    except KeyboardInterrupt:
        return None
