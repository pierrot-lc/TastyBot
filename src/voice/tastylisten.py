import os
import typing
import random
import asyncio

import discord
from discord.ext.commands import Cog, Bot, Context, command

import pandas as pd

from src.voice.voice_manager import VoiceManager


class HandleSongs:
    """All specific functions to manipulate songs.
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
        """Return a path to a random song.
        """
        path_id = random.randrange(0, len(self.df_music))
        return self.df_music['path'].values[path_id]

    def random_playlist(self) -> list:
        """Return a random playlist containing all songs in the df_music.
        """
        return list(self.df_music['path'].sample(frac=1).values)

    def random_album(self) -> list:
        """Return a playlist containing a random album.
        """
        albums = self.df_music.groupby('album')
        album_id = random.randrange(0, len(albums))
        album_name = list(albums.groups.keys())[album_id]
        return self.album_playlist(album_name), album_name

    def infos(self, path: str) -> tuple:
        """Return the song, album and artist of the song path.
        """
        df_music = self.df_music
        song = df_music[ df_music['path'] == path ]['song_name'].values[0]
        album = df_music[ df_music['path'] == path ]['album'].values[0]
        artist = df_music[ df_music['path'] == path ]['artist'].values[0]

        return song, album, artist

    def albums(self) -> dict:
        """Dictionnary mapping an album with its songs (path).
        """
        albums = list(self.df_music['album'].unique())
        return {a: self.album_playlist(a) for a in albums}


class TastyListen(Cog):
    """Commands to listen to some Tasty musics.
    """
    def __init__(self, bot: Bot, voice_manager: VoiceManager):
        self.bot = bot
        self.song_handler = HandleSongs()
        self.voice_manager = voice_manager

    @command(name='music')
    async def tastymusic(self, context: Context):
        """Listen to a random playlist of Tastycool Songs.

        You have to be connected to a voice channel.
        """
        if not await self.voice_manager.connect(context):
            return  # Connexion to voice client failed

        guild_id = context.guild.id
        self.voice_manager.empty_playlist(guild_id)

        for path in self.song_handler.random_playlist():
            self.voice_manager.add_to_playlist(guild_id, get_audiosource, [path])

        await self.voice_manager.play_next(guild_id)

    @command(name='album')
    async def tastyalbum(
        self,
        context: Context,
        *album_name: typing.Optional[str]
    ):
        """Listen to a tasty album.

        If no arguments are given, a random album is being played.
        You have to be connected to a voice channel.
        """
        if not await self.voice_manager.connect(context):
            return  # Connexion to voice client failed

        guild_id = context.guild.id

        if album_name:
            album_name = ' '.join(album_name)
            playlist = self.song_handler.album_playlist(album_name)
            if not playlist:  # Album not found
                await context.send(f'Album {album_name} not found.')
                return
        else:
            playlist, album_name = self.song_handler.random_album()
            await context.send(f'Playing {album_name}.')

        self.voice_manager.empty_playlist(guild_id)
        for path in playlist:
            self.voice_manager.add_to_playlist(guild_id, get_audiosource, [path])

        await self.voice_manager.play_next(guild_id)

    @command()
    async def tastycool(self, context: Context):
        """List the songs that I have in my bag.
        """
        desc = '```\n'

        for album_name, paths in self.song_handler.albums().items():
            desc += f'{album_name}:\n'
            for song_id, path in enumerate(paths):
                song_name, _, _ = self.song_handler.infos(path)
                desc += f'\t{song_id+1}. {song_name}\n'
            desc += '\n'

        desc += '```'
        await context.send(desc)  # Remove the last '\n'


async def get_audiosource(path: str) -> tuple[discord.FFmpegPCMAudio, str]:
    """Read the file and return the corresponding audio source.
    """
    audio_source = discord.FFmpegPCMAudio(path)
    audio_source = discord.PCMVolumeTransformer(audio_source, 0.3)
    return audio_source, path
