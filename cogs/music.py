import random
from pathlib import Path

import discord
from discord.ext import commands

from jukebot import Jukebot

NEO_JUKEBOX = 1077343507343212585
MUSIC_DIR = Path("./music")

MUSIC_COOLDOWN = commands.CooldownMapping.from_cooldown(  # shared cooldown
    rate=1, per=5, type=commands.BucketType.guild
)


def get_songs() -> list[str]:
    """Returns a list of all mp3 files in the music directory"""
    # because doing this at module level isn't great when I add songs at runtime
    return list(sorted(p.name for p in Path(MUSIC_DIR).glob("**/*.mp3")))


async def songs_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[discord.app_commands.Choice[str]]:
    songs = get_songs()

    if not current:
        # if the user hasn't typed anything yet, shuffle the songs so they come up randomly
        # this is better than just showing the top alphabetical songs for visibility purposes.
        random.shuffle(songs)

    filtered_songs = [s for s in songs if s.lower().startswith(current.lower())][:25]

    return [
        discord.app_commands.Choice(name=Path(s).stem, value=s) for s in filtered_songs
    ]


class Music(commands.Cog):
    def __init__(self, bot: Jukebot) -> None:
        self.bot = bot

    async def play_song(
        self, interaction: discord.Interaction, *, song_path: str
    ) -> None:
        """Plays a song from the local filesystem"""
        assert interaction.guild is not None
        assert interaction.guild.voice_client is not None

        song_file = MUSIC_DIR / song_path

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                str(song_file),
                before_options="-stream_loop -1",  # loop forever
            )
        )

        interaction.guild.voice_client.play(  # type: ignore
            source, after=lambda e: print(f"Player error: {e}") if e else None  # type: ignore
        )

        await interaction.response.send_message(
            f"Now playing: `{song_file.stem}` \N{MULTIPLE MUSICAL NOTES}",
        )

    @discord.app_commands.command(
        name="play", description="Plays a song from the local filesystem"
    )
    @discord.app_commands.autocomplete(song=songs_autocomplete)
    @discord.app_commands.describe(song="The Neopets song you're looking for")
    async def play_slash(self, interaction: discord.Interaction, song: str) -> None:
        if song not in get_songs():
            await interaction.response.send_message(
                f"Song `{song}` not found.", ephemeral=True
            )
            return
        await self.ensure_voice(interaction)
        await self.play_song(interaction, song_path=song)

    async def ensure_voice(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None

        if interaction.guild.voice_client is None:
            assert interaction.user is not None
            assert isinstance(interaction.user, discord.Member)
            if interaction.user.voice:
                assert interaction.user.voice.channel is not None

                if interaction.user.voice.channel.id != NEO_JUKEBOX:
                    await interaction.response.send_message(
                        f"You are not in the <#{NEO_JUKEBOX}> channel.", ephemeral=True
                    )
                    raise commands.CommandError(f"Author not in <#{NEO_JUKEBOX}>.")
                await interaction.user.voice.channel.connect()
            else:
                await interaction.response.send_message(
                    "You are not connected to a voice channel.", ephemeral=True
                )
                raise commands.CommandError("Author not connected to a voice channel.")
        elif interaction.guild.voice_client.is_playing():  # type: ignore
            interaction.guild.voice_client.stop()  # type: ignore


async def setup(bot: Jukebot) -> None:
    await bot.add_cog(Music(bot))
