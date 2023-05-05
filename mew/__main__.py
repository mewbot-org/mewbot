"""
Unless otherwise mentioned, source code in this repository is owned by the Mewbot Developers mentioned in README.md in the root of this repository.
This source code is un-licensed.  As such, standard copyright laws apply.
Any unauthorized access, distribution, or use is strictly prohibited.
"""
import sys
import os

if not os.path.isdir(sys.argv[6]):
    raise RuntimeError("Invalid app directory: not a directory")

if "DIRECTORY" not in os.environ:
    os.environ["DIRECTORY"] = sys.argv[6]

from mewcore.dna import Mew
from pathlib import Path
from flask import Flask
import sentry_sdk
import functools
import logging
import asyncio
import signal
import time
import json


class SIGINTController(object):
    def __init__(self, bot, logger=None):
        self.bot = bot
        self.logger = logger

    def __enter__(self):
        self.old_handler = signal.signal(signal.SIGINT, self.wrapper)
        self.old_term_handler = signal.signal(signal.SIGTERM, self.sigterm_wrapper)

    def wrapper(self, *args):
        asyncio.create_task(self.handler())

    def sigterm_wrapper(self, *args):
        asyncio.create_task(self.sigterm_handler())

    async def handler(self):
        if self.logger:
            self.logger.debug(
                "Received SIGINT signal.  If attempting to stop outside the cluster, please use SIGTERM"
            )

    async def sigterm_handler(self):
        if self.logger:
            self.logger.info(
                "Received SIGTERM signal.  Please do not use this if the cluster was created through the launcher."
            )
        await self.bot.close()

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        signal.signal(signal.SIGTERM, self.old_term_handler)


def parse_cluster_info():
    # Temporary statement until the next bot restart
    if len(sys.argv) == 6:
        sys.argv.append("/home/dyroot/mewbot/")

    if not len(sys.argv) == 7:
        raise RuntimeError(
            "Invalid arguments passed.\nUsage: [shard_list...] shard_count cluster_id cluster_name logging_code app_dir"
        )

    try:
        shards = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise RuntimeError(
            "Invalid shard list: must be a list of shards that is JSON serializable"
        )

    try:
        total_shards = int(sys.argv[2])
    except ValueError:
        raise RuntimeError("Invalid shard count: Must be integer")

    try:
        id_ = int(sys.argv[3])
    except ValueError:
        raise RuntimeError("Invalid cluster ID: Must be integer")

    name = sys.argv[4]

    try:
        logging_code = int(sys.argv[5])
        assert 0 <= logging_code <= 3
    except (ValueError, AssertionError):
        raise RuntimeError("Invalid logging code: Must be integer in range 0 - 3")

    info = {
        "shards": shards,
        "total_shards": total_shards,
        "id": id_,
        "name": name,
        "lc": logging_code,
        "ad": Path(sys.argv[6]),
    }
    return info


def initialize_logging(cluster_id, cluster_name, logging_code):
    dpy_logger = logging.getLogger("discord")
    base_logger = logging.getLogger("mewbot")

    if logging_code == 0:
        dpy_logger.setLevel(logging.WARNING)
        base_logger.setLevel(logging.INFO)
    elif logging_code == 1:
        dpy_logger.setLevel(logging.WARNING)
        base_logger.setLevel(logging.DEBUG)
    elif logging_code == 2:
        dpy_logger.setLevel(logging.DEBUG)
        base_logger.setLevel(logging.INFO)
    elif logging_code == 3:
        dpy_logger.setLevel(logging.DEBUG)
        base_logger.setLevel(logging.DEBUG)
    else:
        raise RuntimeError("Invalid logging code")

    formatter = logging.Formatter(
        f"[%(asctime)-19s] [%(levelname)-8s]: [Cluster #{cluster_id} ({cluster_name})] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    base_logger.addHandler(stdout_handler)
    dpy_logger.addHandler(stdout_handler)

    return base_logger


if __name__ == "__main__":
    info = parse_cluster_info()
    logger = initialize_logging(info["id"], info["name"], info["lc"])

    client = Mew(info)

    try:
        with SIGINTController(client, logger):
            asyncio.run(client._run())
    except Exception as e:
        logger.critical("Ran into a critical error!", exc_info=True)
    finally:
        sys.exit(0)
