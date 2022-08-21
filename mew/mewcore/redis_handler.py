import os
from discord.ext import commands
from contextlib import suppress, redirect_stdout
from async_timeout import timeout
from datetime import datetime
from uuid import uuid4
import traceback
import textwrap
import orjson
import asyncio
import aiohttp
import inspect
import discord
import time
import io


class RedisHandler:
    """Class to receive events from Redis and manage other notifications"""

    def __init__(self, bot):
        self.bot = bot
        self.cluster = bot.cluster
        self.logger = bot.logger
        self.redis = None

        self._messages = dict()

    async def start(self):
        self.redis = self.bot.db[2]
        asyncio.create_task(self.cluster_handler())

    async def cluster_handler(self):
        await self.redis.execute_pubsub("SUBSCRIBE", os.environ["MEWLD_CHANNEL"])
        channel = self.redis.pubsub_channels[bytes(os.environ["MEWLD_CHANNEL"], "utf-8")]

        while await channel.wait_message():
            try:
                payload = await channel.get_json(encoding="utf-8")
            except orjson.JSONDecodeError:
                continue  # not a valid JSON message

            if payload.get("diag"):
                try:
                    if self.cluster["id"] != payload["id"]:
                        self.logger.info(f"Got diag message for (different) cluster {payload['id']}. Ignoring...")
                        continue
                    self.logger.info(f"Got diag message for cluster {payload['id']}")
                    
                    shards = []
                    for shard_id, shard in self.bot.shards.items():
                        shards.append({
                            "id": shard_id,
                            "latency": shard.latency,
                            "up": True,
                            "guilds": len(self.bot.guilds),
                        })
                
                    sPayload = {
                        "scope": "launcher",
                        "action": "diag",
                        "output": orjson.dumps({
                            "data": shards,
                            "nonce": payload["nonce"],
                        }).decode()
                    }

                    await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(sPayload))
                except Exception as e:
                    self.logger.error("Exception in cluster_handler", exc_info=True)
                    continue

            if payload.get("scope") != "bot":
                continue

            if payload.get("action") and hasattr(self, payload.get("action")):
                args = payload.get("args", {})
                asyncio.create_task(
                    getattr(self, payload["action"])(args, command_id=payload["command_id"])
                )

            if payload.get("output") and payload["command_id"] in self._messages:
                self._messages[payload["command_id"]].append(payload["output"])

    async def handler(
        self,
        action: str,
        expected_count: int,
        args: dict = {},
        _timeout: int = 2,
        scope: str = "bot",
        output: dict = {},
    ):
        command_id = str(uuid4())
        self._messages[command_id] = []

        payload = {"scope": scope, "action": action, "command_id": command_id}
        if args:
            payload["args"] = args
        
        if output:
            payload["output"] = output

        await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))

        with suppress(asyncio.TimeoutError):
            async with timeout(_timeout):
                while len(self._messages[command_id]) < expected_count:
                    await asyncio.sleep(0.1)
        return self._messages.pop(command_id, None)

    async def shutdown(self, args, *, command_id):
        if args.get("cluster_id") == self.cluster["id"]:
            if not args.get("yesiknowwhatimdoingpleasedontspammessages"):
                self.logger.info("Received shutdown request from Redis")
            else:
                self.logger.debug("Received shutdown request from Redis")
            await self.bot.logout()

    async def send_cluster_info(self, args, *, command_id: str):
        try:
            try:
                latency = round(self.bot.latency * 1000)
            except OverflowError:
                latency = "infinity"

            guilds = 0
            channels = 0
            users = 0

            for g in self.bot.guilds:
                guilds += 1
                channels += len(g.channels)
                users += g.member_count or 0

            payload = {
                "output": {
                    "id": self.cluster["id"],
                    "name": f"{self.cluster['name']}",
                    "latency": latency,
                    "guilds": guilds,
                    "channels": channels,
                    "users": users,
                    "shards": self.cluster["shards"],
                },
                "command_id": command_id,
                "scope": "bot",
            }

            await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))
        except Exception as e:
            self.logger.error("Exception in send_cluster_info", exc_info=True)

    async def send_shard_info(self, args, *, command_id: str):
        try:
            if args["cluster_id"] != self.cluster["id"]:
                return
            shard_groups = {}
            for shard_id, shard in self.bot.shards.items():
                lat = "inf"
                with suppress(OverflowError):
                    lat = round(shard.latency * 1000)
                shard_groups[str(shard_id)] = {
                    "id": shard_id + 1,
                    "latency": lat,
                    "guilds": 0,
                    "channels": 0,
                    "users": 0,
                }

            for g in self.bot.guilds:
                shard_groups[str(g.shard_id)]["guilds"] += 1
                shard_groups[str(g.shard_id)]["channels"] += len(g.channels)
                shard_groups[str(g.shard_id)]["users"] += g.member_count or 0

            payload = {
                "output": {
                    "id": self.cluster["id"],
                    "name": self.cluster["name"],
                    "shards": shard_groups,
                },
                "command_id": command_id,
                "scope": "bot",
            }
            await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))
        except Exception as e:
            self.logger.error("Exception in send_shard_inf", exc_info=True)

    async def load(self, args, *, command_id: str):
        output = {}
        try:
            for cog in args["cogs"]:
                try:
                    await self.bot.load_extension(cog)
                except Exception as e:
                    output[cog] = {"success": False, "message": f"{type(e).__name__}: {str(e)}"}
                else:
                    output[cog] = {"success": True, "message": ""}
            if "silent" in args and args["silent"]:
                return output
            else:
                payload = {
                    "output": {"cluster_id": self.cluster["id"], "cogs": output},
                    "command_id": command_id,
                    "scope": "bot",
                }
                await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))
        except Exception as e:
            self.logger.error("Exception in redis load", exc_info=True)
            return {}

    async def unload(self, args, *, command_id: str):
        output = {}
        try:
            for cog in args["cogs"]:
                try:
                    await self.bot.unload_extension(cog)
                except Exception as e:
                    output[cog] = {"success": False, "message": f"{type(e).__name__}: {str(e)}"}
                else:
                    output[cog] = {"success": True, "message": ""}
            if "silent" in args and args["silent"]:
                return output
            else:
                payload = {
                    "output": {"cluster_id": self.cluster["id"], "cogs": output},
                    "command_id": command_id,
                    "scope": "bot",
                }
                await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))
        except Exception as e:
            self.logger.error("Exception in redis unload", exc_info=True)
            return {}

    async def _eval(self, args, *, command_id: str):
        if args["cluster_id"] != self.cluster["id"] and args["cluster_id"] != "-1":
            return

        start = time.time()
        startTime = datetime.now()

        env = {
            "bot": self.bot,
            "asyncio": asyncio,
            "aiohttp": aiohttp,
            "json": orjson,
            "discord": discord,
            "commands": commands,
            "source": inspect.getsource,
        }
        env.update(globals())

        body = args["body"]
        stdout = io.StringIO()
        out = None

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
            total_time = datetime.now() - startTime
            end = time.time()
            total_time2 = end - start
        except Exception as e:
            payload = {
                "output": {
                    "cluster_id": self.cluster["id"],
                    "type": "error",
                    "message": f"{e.__class__.__name__}: {e}"
                },
                "command_id": command_id,
                "scope": "bot"
            }
            return await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            payload = {
                "output": {
                    "cluster_id": self.cluster["id"],
                    "type": "error",
                    "message": f"{value}{traceback.format_exc()}"
                },
                "command_id": command_id,
                "scope": "bot"
            }
            return await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))
        value = stdout.getvalue()
        if ret is None:
            if value:
                payload = {
                    "output": {
                        "cluster_id": self.cluster["id"],
                        "type": "success",
                        "message": str(value)
                    },
                    "command_id": command_id,
                    "scope": "bot"
                }
                return await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))
        else:
            payload = {
                "output": {
                    "cluster_id": self.cluster["id"],
                    "type": "success",
                    "message": f"{value}{ret}"
                },
                "command_id": command_id,
                "scope": "bot"
            }
            return await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))
        payload = {
            "output": {
                "cluster_id": self.cluster["id"],
                "type": "success",
                "message": ""
            },
            "command_id": command_id,
            "scope": "bot"
        }
        return await self.redis.execute("PUBLISH", os.environ["MEWLD_CHANNEL"], orjson.dumps(payload))

    async def all_clusters_launched(self, args, *, command_id: str):
        self.bot._clusters_ready.set()
