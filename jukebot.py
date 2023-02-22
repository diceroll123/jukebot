import asyncio
import ctypes
import ctypes.util
import os
import sys
from typing import Any

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

discord.opus.load_opus(ctypes.util.find_library("opus"))  # type: ignore

intents = discord.Intents.all()

initial_extensions = [
    "cogs.music",
    "cogs.debug",
]


class Jukebot(commands.Bot):
    initial_extensions: list[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.initial_extensions = initial_extensions

    async def start_extensions(self) -> None:
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                import traceback

                traceback.print_exc()
                print(f"Failed to load extension {extension}\n{type(e).__name__}: {e}")

    async def setup_hook(self) -> None:
        assert self.user is not None

        print(f"Logged in as {self.user} (ID: {self.user.id})")
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id

        try:
            await self.start_extensions()
        except Exception:
            import traceback

            traceback.print_exc()
            sys.exit(1)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)


async def main() -> None:
    bot = Jukebot(
        command_prefix=commands.when_mentioned_or("$"),
        intents=intents,
    )
    async with bot:
        await bot.start(os.getenv("BOT_TOKEN"))  # type: ignore


if __name__ == "__main__":  # so this doesn't get run when we import it
    asyncio.run(main())
