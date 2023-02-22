import random
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext.commands import Context

from jukebot import Jukebot

from .utils import checks

NEO_JUKEBOX = 1077343507343212585
MUSIC_DIR = Path("./music")

MUSIC_COOLDOWN = commands.CooldownMapping.from_cooldown(  # shared cooldown
    rate=1, per=5, type=commands.BucketType.guild
)


def get_song_index(songs: list[str], song_name: str) -> int | None:
    """Returns the index of the song in the list of songs"""
    try:
        return songs.index(song_name)
    except ValueError:
        return None


class Music(commands.Cog):
    def __init__(self, bot: Jukebot) -> None:
        self.bot = bot

    @property
    def songs(self) -> list[str]:
        """Returns a list of all mp3 files in the music directory"""
        # because doing this at module level isn't great when I add songs at runtime
        return list(sorted(p.name for p in Path(MUSIC_DIR).glob("**/*.mp3")))

    async def play_song(self, ctx: Context[Jukebot], *, song_path: str) -> None:
        """Plays a song from the local filesystem"""
        assert ctx.guild is not None
        assert ctx.voice_client is not None

        song_file = MUSIC_DIR / song_path

        # to keep state of what's playing (or last played,) in which server
        self.bot.currently_playing[ctx.guild.id] = song_file.name

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                str(song_file),
                before_options="-stream_loop -1",  # loop forever
            )
        )

        ctx.voice_client.play(  # type: ignore
            source, after=lambda e: print(f"Player error: {e}") if e else None  # type: ignore
        )

        await ctx.reply(
            f"Now playing: `{song_file.name}` \N{MULTIPLE MUSICAL NOTES}",
            allowed_mentions=discord.AllowedMentions(replied_user=False),
        )

    @commands.command(cooldown=MUSIC_COOLDOWN)
    @checks.is_in_channel(NEO_JUKEBOX)
    async def shuffle(self, ctx: Context[Jukebot]) -> None:
        """Plays a random song from the local filesystem"""
        assert ctx.guild is not None
        songs = self.songs

        current_song_index = get_song_index(
            songs, self.bot.currently_playing[ctx.guild.id]
        )
        if current_song_index is not None:
            songs.pop(current_song_index)

        await self.play_song(ctx, song_path=random.choice(songs))

    @commands.command(cooldown=MUSIC_COOLDOWN)
    @checks.is_in_channel(NEO_JUKEBOX)
    async def next(self, ctx: Context[Jukebot]) -> None:
        """Plays the next song from the local filesystem"""
        assert ctx.guild is not None
        songs = self.songs

        current_song_index = get_song_index(
            songs, self.bot.currently_playing[ctx.guild.id]
        )
        if current_song_index is None:
            current_song_index = -1

        song = songs[(current_song_index + 1) % len(songs)]
        await self.play_song(ctx, song_path=song)

    @commands.command(aliases=["prev"], cooldown=MUSIC_COOLDOWN)
    @checks.is_in_channel(NEO_JUKEBOX)
    async def previous(self, ctx: Context[Jukebot]) -> None:
        """Plays the previous song from the local filesystem"""
        assert ctx.guild is not None
        songs = self.songs

        current_song_index = (
            get_song_index(songs, self.bot.currently_playing[ctx.guild.id]) or 0
        )

        song = songs[current_song_index - 1]
        await self.play_song(ctx, song_path=song)

    @commands.command()
    @commands.is_owner()
    @checks.is_in_channel(NEO_JUKEBOX)
    async def play(self, ctx: Context[Jukebot], *, song: str) -> None:
        """Plays a file from the local filesystem"""
        await self.play_song(ctx, song_path=song)

    @commands.command()
    @commands.is_owner()
    @checks.is_in_channel(NEO_JUKEBOX)
    async def stop(self, ctx: Context[Jukebot]) -> None:
        """Stops and disconnects the bot from voice"""
        assert ctx.voice_client is not None

        await ctx.voice_client.disconnect()  # type: ignore

    @play.before_invoke
    @shuffle.before_invoke
    @next.before_invoke
    @previous.before_invoke
    async def ensure_voice(self, ctx: Context[Jukebot]) -> None:
        if ctx.voice_client is None:
            assert ctx.author is not None
            assert isinstance(ctx.author, discord.Member)
            if ctx.author.voice:
                assert ctx.author.voice.channel is not None

                if ctx.author.voice.channel.id != NEO_JUKEBOX:
                    await ctx.reply("You are not in the Neo Jukebox.")
                    raise commands.CommandError(f"Author not in <#{NEO_JUKEBOX}>.")
                await ctx.author.voice.channel.connect()
            else:
                await ctx.reply("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


async def setup(bot: Jukebot) -> None:
    await bot.add_cog(Music(bot))
