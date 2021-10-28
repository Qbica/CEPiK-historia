import os
from datetime import datetime
from pathlib import Path


class Logger:

    _path = None

    @staticmethod
    def get_path():
        if Logger._path is None:
            Logger.new_file()

        return Logger._path

    @staticmethod
    def new_file():
        Path("logs").mkdir(parents=True, exist_ok=True)
        file = f"log_{datetime.now().strftime('%Y_%m_%d %H_%M_%S')}.txt"
        Logger._path = os.path.join("logs", file)

    @staticmethod
    def _log(msg, level):
        full_msg = f"[{level}] {datetime.now()} | {msg}"

        print(full_msg)

        try:
            with open(Logger.get_path(), "a") as file:
                file.write(f"{full_msg}\n")
        except Exception as error:
            print(f"Logger error: {error}")

    @staticmethod
    def info(msg):
        Logger._log(msg, "INFO")

    @staticmethod
    def warn(msg):
        Logger._log(msg, "WARN")

    @staticmethod
    def error(msg):
        Logger._log(msg, "ERROR")
