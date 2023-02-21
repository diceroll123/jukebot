import asyncio
from contextlib import suppress

import discord
from discord.ext import commands
from discord.ext.commands import Context

from jukebot import Jukebot

NEO_GUILD = 123668853698854913


class Debug(commands.Cog):
    def __init__(self, bot: Jukebot) -> None:
        self.bot = bot

    @commands.command(aliases=["reload", "restart"])
    @commands.is_owner()
    async def load(self, ctx: Context[Jukebot], module: str = "") -> None:
        """Reloads modules"""
        try:
            if not module:
                for extension in ctx.bot.initial_extensions:
                    if extension in ctx.bot.extensions:
                        await ctx.bot.reload_extension(extension)
                    else:
                        await ctx.bot.load_extension(extension)
            else:
                await ctx.bot.reload_extension(f"cogs.{module}")

        except Exception:
            import traceback

            await ctx.message.add_reaction("\N{CROSS MARK}")
            await ctx.send(traceback.format_exc())
        else:
            with suppress(Exception):
                await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
                await asyncio.sleep(1)
                await ctx.message.delete()

    @commands.command()
    @commands.is_owner()
    async def debug(self, ctx: Context[Jukebot], *, code: str) -> None:
        """Evaluates code."""
        code = code.strip("` ")
        python = "```py\n{0}\n```"

        env = {
            "ctx": ctx,
            "bot": ctx.bot,
            "message": ctx.message,
            "guild": ctx.guild,
            "channel": ctx.channel,
            "category": getattr(ctx.channel, "category", None),
            "author": ctx.author,
            "discord": discord,
            "neo": ctx.bot.get_guild(NEO_GUILD),
            "neoguild": ctx.bot.get_guild(NEO_GUILD),
        } | globals()

        try:
            result = eval(code, env)
            import inspect

            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await ctx.send(python.format(f"{type(e).__name__}: {str(e)}"))
            return
        await ctx.send(python.format(result))


async def setup(bot: Jukebot) -> None:
    await bot.add_cog(Debug(bot))
