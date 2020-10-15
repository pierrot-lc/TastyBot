import os
import typing
import random
import asyncio

import discord
from discord.ext.commands import Cog, Bot, Context, command

import pandas as pd


class GuildState:
    """
    Contains all informations about a
    guild state concerning voice channels
    and listened songs.
    """
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.voice_client = None
        self.currently_playing = None
        self.playlist = list()


class HandleSongs:
    """
    All specific functions
    to manipulate songs.
    """
    def __init__(self):
        self.df_music = pd.read_csv('songs.csv', sep=',')

    def album_playlist(self, album_name: str) -> list:
        """
        Return the playlist for the given album.
        """
        if not album_name in self.df_music['album'].values:
            return None
        album = self.df_music[ self.df_music['album'] == album_name ]
        album = album.sort_values(by='song_id')
        return list(album['path'].values)

    def random_song(self) -> str:
        """
        Return a path
        to a random song.
        """
        path_id = random.randrange(0, len(self.df_music))
        return self.df_music['path'].values[path_id]

    def random_playlist(self) -> list:
        """
        Return a random
        playlist containing all
        songs in the df_music.
        """
        return list(self.df_music['path'].sample(frac=1).values)

    def random_album(self) -> list:
        """
        Return a playlist containing
        a random album.
        """
        albums = self.df_music.groupby('album')
        album_id = random.randrange(0, len(albums))
        album_name = list(albums.groups.keys())[album_id]
        return self.album_playlist(album_name), album_name

    def infos(self, path: str) -> tuple:
        """
        Return the song, album and artist of
        the song path.
        """
        df_music = self.df_music
        song = df_music[ df_music['path'] == path ]['song_name'].values[0]
        album = df_music[ df_music['path'] == path ]['album'].values[0]
        artist = df_music[ df_music['path'] == path ]['artist'].values[0]

        return song, album, artist

    def albums(self) -> dict:
        """
        Dictionnary mapping an album with its
        songs (path).
        """
        albums = list(self.df_music['album'].unique())
        return {a: self.album_playlist(a) for a in albums}


class TastyListen(Cog):
    """
    Commands to listen to some
    Tasty musics.
    """
    def __init__(self, bot: Bot):
        self.bot = bot
        self.song_handler = HandleSongs()
        self.guild_states = dict()  # guild.id -> GuildSate

    def get_guildstate(self, guild_id):
        """
        Return the GuildState associated with the
        guild_id.
        """
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = GuildState(guild_id)
        return self.guild_states[guild_id]

    @command(name='music')
    async def tastymusic(self, context: Context):
        """
        Listen to a random playlist.
        """
        voice = context.author.voice
        guild = context.guild
        if voice is None:  # Sender isn't connected to a voice channel
            await context.send('You have to be connected to'+
                    'a voice channel to listen to some Tasty songs !')
            return

        gs = self.get_guildstate(guild.id)

        if gs.voice_client and\
                gs.voice_client.channel != voice.channel:
            # Changing voice channel
            if gs.voice_client.is_connected():
                await gs.voice_client.disconnect()
            gs.voice_client = None

        if gs.voice_client is None:
            gs.voice_client = await voice.channel.connect()

        playlist = self.song_handler.random_playlist()

        if gs.voice_client.is_playing():
            gs.playlist = playlist
            gs.voice_client.stop()
            return

        path = playlist.pop(0)
        gs.playlist = playlist
        song_audiosource = discord.FFmpegPCMAudio(path)
        song_audiosource = discord.PCMVolumeTransformer(song_audiosource, 0.3)

        gs.voice_client.play(song_audiosource, after=lambda e: self.after_play(e, gs))
        gs.currently_playing = path

    @command(name='album')
    async def tastyalbum(self, context: Context,
            *album_name: typing.Optional[str]):
        """
        Listen to a tasty album.

        If no arguments are given, a random album is being played.
        """
        voice = context.author.voice
        if voice is None:  # Sender isn't connected to a voice channel
            await context.send('You have to be connected to'+
                    'a voice channel to listen to some Tasty songs !')
            return

        if album_name:
            album_name = ' '.join(album_name)
            playlist = self.song_handler.album_playlist(album_name)
            if not playlist:  # Album not found
                await context.send(f'Album {album_name} not found.')
                return
            gs.playlist = playlist
        else:
            gs.playlist, album_name = self.song_handler.random_album()
            await context.send(f'Playing {album_name}.')

        gs = self.get_guildstate(context.guild.id)
        if gs.voice_client and\
                gs.voice_client.channel != voice.channel:
            # Changing voice channel
            if gs.voice_client.is_connected():
                await gs.voice_client.disconnect()
            gs.voice_client = None

        if not gs.voice_client:
            gs.voice_client = await voice.channel.connect()

        if gs.voice_client.is_playing():
            gs.voice_client.stop()  # Go to after_play
            return

        path = gs.playlist.pop(0)
        song_audiosource = discord.FFmpegPCMAudio(path)
        song_audiosource = discord.PCMVolumeTransformer(song_audiosource, 0.3)

        gs.voice_client.play(song_audiosource, after=lambda e: self.after_play(e, gs))
        gs.currently_playing = path

    @command(name='stop')
    async def tastystop(self, context: Context):
        """
        Stop the current song.
        """
        voice = context.author.voice
        guild = context.guild
        gs = self.get_guildstate(guild.id)

        if gs.voice_client is None or not gs.voice_client.is_connected() or\
                not gs.voice_client.is_playing():
            await context.send('I am not playing anything right not.')
            return

        if voice is None or voice.channel != gs.voice_client.channel:
            await context.send("You're not connected to the same voice channel as me.")
            return

        await gs.voice_client.disconnect()
        gs.voice_client = None
        gs.currently_playing = None
        gs.playlist = []

    @command(name='next')
    async def tastynext(self, context: Context):
        """
        Pass to the next song in the playlist.

        If there are no songs next, disconnect the bot
        from the channel.
        """
        voice = context.author.voice
        guild = context.guild
        gs = self.get_guildstate(guild.id)

        if gs.voice_client is None or not gs.voice_client.is_connected() or\
                not gs.voice_client.is_playing():
            await context.send('I am not playing anything right not.')
            return

        if voice is None or voice.channel != gs.voice_client.channel:
            await context.send("You're not connected to the same voice channel as me.")
            return

        gs.voice_client.stop()  # Calls after_play (which does what we want)

    def after_play(self, error, gs: GuildState):
        """
        Called when a song is finished.

        The bot either plays the next song if there is one,
        or disconnect.
        """
        if not gs.voice_client or\
                not gs.voice_client.is_connected():
            return  # Nothing to do

        if gs.playlist == []:  # Nothing to play next
            coro = gs.voice_client.disconnect()
            gs.voice_client = None
            gs.currently_playing = None
            asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            return

        # Plays the next song
        gs.currently_playing = gs.playlist.pop(0)
        song_audiosource = discord.FFmpegPCMAudio(gs.currently_playing)
        song_audiosource = discord.PCMVolumeTransformer(song_audiosource, 0.4)
        gs.voice_client.play(song_audiosource, after=lambda e: self.after_play(e, gs))

    @command()
    async def playlist(self, context: Context):
        """
        Print the current playlist.
        """
        gs = self.get_guildstate(context.guild.id)
        if not gs.voice_client or not gs.voice_client.is_playing():
            await context.send('The playlist is empty.')
            return

        infos = self.song_handler.infos(gs.currently_playing)
        playlist_desc = 'Currently playing:\n'
        playlist_desc += f'\t{infos[0]} - {infos[1]} - {infos[2]}'

        if gs.playlist:
            playlist_desc += '\n\nPlaylist:\n'
        for song_number, path in enumerate(gs.playlist):
            infos = self.song_handler.infos(path)
            playlist_desc += f'\t{song_number+1}. {infos[0]} - {infos[1]} - {infos[2]}\n'

        await context.send(playlist_desc)

    @command()
    async def tastycool(self, context: Context):
        """
        List the songs that I have in my bag.
        """
        desc = ''
        for album_name, paths in self.song_handler.albums().items():
            desc += f'{album_name}:\n'
            for song_id, path in enumerate(paths):
                song_name, _, _ = self.song_handler.infos(path)
                desc += f'\t{song_id+1}. {song_name}\n'
            desc += '\n'

        await context.send(desc[:-1])  # Remove the last '\n'
