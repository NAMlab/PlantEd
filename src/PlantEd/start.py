import argparse
import atexit
import logging
import multiprocessing
import signal
import sys
import time
from pathlib import Path

from PlantEd import game
from PlantEd.server.server import Server

logger = logging.getLogger(__name__)

global server
server:Server

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--logLevel",
        type=str,
        default="WARNING",
        metavar="",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the detail of the log events (default: %(default)s)",
    )

    parser.add_argument(
        "--logFile",
        type=str,
        default="",
        metavar="",
        help="The folder where all log files will be stored. "
             "The log files inside this folder will be overwritten. "
             "The Folder will be created automatically. "
             "By default, no folders or logfiles are created.",
    )

    parser.add_argument(
        "--windowed",
        action='store_true',
        help="Should start the PlantEd full screen or windowed. "
             "Setting this flag results in a windowed start.",
    )

    parser.add_argument(
        "--noUI",
        action='store_true',
        help="noUI flag ensures that only the server is started. Please "
             "refer to the console for the port and interface used.",
    )

    args = parser.parse_args()

    # Default Logger to console and if requested to file
    log_file_defined = (args.logFile != "")
    log_handlers = [logging.StreamHandler(sys.stdout)]

    if log_file_defined:
        path = Path(args.logFile)
        if not path.exists():
            path.mkdir()

        log_handlers.append(
            logging.FileHandler(filename= path / "complete.log", mode="w+")
        )

    for handler in log_handlers:
        handler.setLevel(args.logLevel)

    logging.basicConfig(
        level=args.logLevel,
        format="%(asctime)s %(name)s %(levelname)s:%(message)s",
        datefmt="%H:%M:%S",
        handlers= log_handlers,
    )

    if log_file_defined:
        FORMAT = logging.Formatter("%(asctime)s %(name)s %(levelname)s:%(message)s")

        logger_ui = logging.getLogger("PlantEd.ui")
        handler_ui = logging.FileHandler(
                filename=path / "ui.log",
                mode="w+",
                encoding="utf-8",
                delay=False,
                errors=None,
            )
        handler_ui.setFormatter(FORMAT)
        logger_ui.addHandler(handler_ui)

        logger_client = logging.getLogger("PlantEd.client")
        handler_client = logging.FileHandler(
                filename= path / "client.log",
                mode= "w+",
                encoding="utf-8",
                delay= False,
                errors= None,
            )
        handler_client.setFormatter(FORMAT)
        logger_client.addHandler(handler_client)

        logger_server = logging.getLogger("PlantEd.server")
        handler_server = logging.FileHandler(
                filename=path / "server.log",
                mode="w+",
                encoding="utf-8",
                delay=False,
                errors=None,
            )
        handler_server.setFormatter(FORMAT)
        logger_server.addHandler(handler_server)

    logger.debug("Creating server")

    global server
    server = Server(only_local=False)
    logger.debug("Starting server")
    server.start()

    # Wait till the server binds to a port
    while server.port is None:
        time.sleep(0.1)


    ui_process = multiprocessing.Process(
        target=game.main,
        kwargs={
            "windowed": args.windowed,
            "port": server.port
        })
    #ui_process.start()
    #ui_process.join()

    if args.noUI:
        signal.signal(signal.SIGINT, lambda *args: __stop_server_process)
        signal.signal(signal.SIGTERM, lambda *args: __stop_server_process)
    else:
        try:
            game.main(
                windowed= args.windowed,
                port= server.port
            )
        finally:
            # make sure that the server stops whether the ui has an error or not
            server.stop()


def __stop_server_process():
    server.stop()


if __name__ == "__main__":
    #multiprocessing.set_start_method("spawn")
    main()
