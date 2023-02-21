from __future__ import annotations

from discord.ext import commands
from discord.ext.commands import Context

from jukebot import Jukebot

__all__ = ("is_in_channel",)


def is_in_channel(*channel_ids: int):
    def predicate(ctx: Context[Jukebot]) -> bool:
        return ctx.channel.id in channel_ids

    return commands.check(predicate)
