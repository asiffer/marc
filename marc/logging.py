import logging

from colorama import Back, Fore, Style, just_fix_windows_console

just_fix_windows_console()


class MarcFormatter(logging.Formatter):
    """Pretty formatter for requests"""

    color_mapper = {
        logging.DEBUG: Style.DIM,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.WHITE + Back.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        record.levelname = (
            self.color_mapper[record.levelno] + record.levelname + Style.RESET_ALL
        )
        return super().format(record)


class ServerFormatter(logging.Formatter):
    """Pretty formatter for requests"""

    def format(self, record: logging.LogRecord) -> str:
        # backup values
        msg = record.msg
        args = tuple(record.args)

        col = Fore.RESET
        if record.status_code >= 200 and record.status_code < 300:
            col = Fore.GREEN
        elif record.status_code >= 300 and record.status_code < 400:
            col = Fore.YELLOW
        elif record.status_code >= 400 and record.status_code < 500:
            col = Fore.RED
        elif record.status_code >= 500:
            col = Fore.MAGENTA

        try:
            # modify args
            record.msg = f"{col}%s{Fore.RESET} {Style.BRIGHT}%s{Style.RESET_ALL} %s {Style.DIM}%sµs{Style.RESET_ALL}"
            record.args = (
                record.args[1],
                *record.args[0].split(" ")[:2],
                record.args[2],
            )
            return super().format(record)
        except BaseException:
            # restore
            record.msg = msg
            record.args = args
            return super().format(record)
