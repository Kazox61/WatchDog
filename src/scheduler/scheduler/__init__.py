from shared import setup_logger
import logging

from shared.config import Config

logger = setup_logger("scheduler", "scheduler.log",
                      Config().webhook_debug_log, logging.DEBUG)
