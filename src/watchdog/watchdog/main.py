import traceback

from shared.config import Config

from watchdog import logger
from watchdog.custom_bot import CustomBot
from watchdog.background import player_websocket

if __name__ == "__main__":
    config = Config()

    try:
        bot = CustomBot(config)
        for extension in config.extensions:
            try:
                bot.load_extension(extension)
            except Exception as error:
                exc = ''.join(traceback.format_exception(type(error),
                                                         error, error.__traceback__, chain=True))
                logger.error(exc)

        bot.loop.create_task(player_websocket())

        bot.run(config.discord_token)
    except BaseException as error:
        print(error)
