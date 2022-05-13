"""Manage voice activity of the bot.
It can connect to a voice channel and stop the music.
"""
import asyncio

import discord
from discord.ext.commands import Cog, Bot, Context, command


class GuildState:
    """Contains all informations about a
    guild state concerning voice channels
    and listened songs.
    """
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.voice_client = None
        self.currently_playing = None
        self.playlist = list()

    async def reset(self):
        """Disconnect from the voice channel if possible,
        and erase the current playlist.
        """
        await self.disconnect()
        self.voice_client = None
        self.currently_playing = None
        self.playlist = []

    async def disconnect(self):
        """Disconnect if possible.
        """
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()

        self.voice_client = None

    def cleanup_source(self):
        """Make sure FFmpeg process is cleaned up.
        """
        if self.voice_client and self.voice_client.source:
            self.voice_client.source.cleanup()


class VoiceManager(Cog):
    """A central object instanciated by the main bot and
    that manage the overall voice activity.

    Its goal is to make sure that the bot is connected only into one voice channel
    per guild at the same time (it can be connected to multiple voice channels across
    different guilds at the same time).
    It also make sure that all ressources are cleaned up.
    """
    def __init__(self, bot: Bot):
        self.bot = bot
        self.guild_states = dict()  # guild.id -> GuildState

    def get_guildstate(self, guild_id: int):
        """Return the GuildState associated with the
        guild_id.
        Instanciate a new GuildState if needed.
        """
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = GuildState(guild_id)
        return self.guild_states[guild_id]

    async def connect(self, context: Context) -> bool:
        """Connect to the author's voice channel (defined by the context).
        If the author is not connected to any voice channel, then it will fail.

        Return True if the bot is connected and False if the operation has failed.
        """
        voice = context.author.voice
        guild = context.guild
        if voice is None:  # Sender isn't connected to a voice channel
            await context.send('You have to be connected to a voice channel!')
            return False

        gs = self.get_guildstate(guild.id)

        if gs.voice_client and gs.voice_client.channel != voice.channel:
            # We have to change the channel the bot is connected to
            gs.disconnect()  # Disconnect the bot

        if gs.voice_client is None:  # Connect the bot to the author's channel
            gs.voice_client = await voice.channel.connect()

        return True

    @command(name='stop')
    async def voice_stop(self, context: Context):
        """Stop the current song.
        """
        voice = context.author.voice
        guild = context.guild
        gs = self.get_guildstate(guild.id)

        if gs.voice_client is None or not gs.voice_client.is_connected() or \
                not gs.voice_client.is_playing():
            await context.send('I am not playing anything right now.')
            return

        if voice is None or voice.channel != gs.voice_client.channel:
            await context.send("You're not connected to the same voice channel as me.")
            return

        await gs.reset()  # Reset all variables

    @command(name='next')
    async def voice_next(self, context: Context):
        """Pass to the next song in the playlist.
        If there are no songs next, disconnect the bot
        from the channel.
        """
        voice = context.author.voice
        guild = context.guild
        gs = self.get_guildstate(guild.id)

        if gs.voice_client is None or not gs.voice_client.is_connected() or\
                not gs.voice_client.is_playing():
            await context.send('I am not playing anything right now.')
            return

        if voice is None or voice.channel != gs.voice_client.channel:
            await context.send("You're not connected to the same voice channel as me.")
            return

        gs.voice_client.stop()  # Calls after_play (which does what we want)

    def empty_playlist(self, guild_id: int):
        """Empty the playlist for the given guild.
        """
        gs = self.get_guildstate(guild_id)
        gs.playlist = []

    def add_to_playlist(self, guild_id: int, fn: callable, args: list):
        gs = self.get_guildstate(guild_id)
        gs.playlist.append((fn, args))

    def is_playing(self, guild_id: int) -> bool:
        gs = self.get_guildstate(guild_id)
        if gs.voice_client is not None and gs.voice_client.is_connected():
            return gs.voice_client.is_playing()
        return False

    async def play_next(self, guild_id: int):
        """Play the next song in the playlist.

        The playlist shouln't be empty.
        The bot should be connected to a voice channel.
        If it is currently playing something, it stops the song and play the next.
        Otherwise, it just plays the next song in the playlist.
        """
        gs = self.get_guildstate(guild_id)
        assert len(gs.playlist) > 0, "Playlist empty!"

        if gs.voice_client.is_playing():
            gs.voice_client.stop()  # Calls after_play => properly clean up ressources and then calls play_next
            return

        fn, args = gs.playlist.pop(0)
        audio_source, infos = await fn(*args)
        gs.voice_client.play(audio_source, after=lambda e: self.after_play(e, guild_id))
        gs.currently_playing = infos
        # await context.send(f'Now playing: {player.title}')

    def after_play(self, error, guild_id: int):
        """Called when a song is finished.
        The bot either plays the next song if there is one,
        or disconnect.
        """
        gs = self.get_guildstate(guild_id)
        if not gs.voice_client or\
                not gs.voice_client.is_connected():
            return  # Nothing to do

        if gs.playlist == []:  # Nothing to play next
            coro = gs.reset()
            asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            return

        # Cleanup ending source
        gs.cleanup_source()
        # Plays the next song
        coro = self.play_next(guild_id)
        asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
