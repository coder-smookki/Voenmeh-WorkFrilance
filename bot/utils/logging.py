from sys import stdout
import logging


log_filename="/var/log/bot/bot.log"

def setup_logger():
    format_logs =  "%(asctime)s - %(levelname)s - %(module)s - %(name)s - %(message)s"
    file_handler = logging.FileHandler(log_filename)
    stdout_handler =  logging.StreamHandler(stream=stdout)

    logging.basicConfig(
        level=logging.INFO, 
        format=format_logs,
        handlers=[file_handler, stdout_handler]
    )
        
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)
    return logger