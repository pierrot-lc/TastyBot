"""Basic Youtube player for discord.

Can stream Youtube sounds from any given URL.
Also implements a queue, a stop and next command, all of this being handled over multiple guilds.

Thanks to @Vinicius Mesquita for his post on SO: https://stackoverflow.com/questions/56060614/how-to-make-a-discord-bot-play-youtube-audio.

Requirements: YoutubDl, ffmpeg, PyNaCl
"""
from typing import Optional

import discord
from discord.ext.commands import Cog, Bot, Context, command

import youtube_dl

from src.voice.voice_manager import VoiceManager


youtube_dl.utils.bug_reports_message = lambda e: print('Error:', e)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(
            cls,
            url: str,
            *,
            loop=None,
            stream: bool = False
        ):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class YoutubeBot(Cog):
    def __init__(self, bot: Bot, voice_manager: VoiceManager):
        self.bot = bot
        self.voice_manager = voice_manager

    @command(name='play')
    async def yt_play(
            self,
            context: Context,
            *,
            url: Optional[str]
        ):
        """Add to the playlist the Youtube song.

        You have to be connected to a voice channel.
        """
        if not await self.voice_manager.connect(context):
            return  # Connexion to voice client failed

        guild_id = context.guild.id

        loop = self.bot.loop
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        if '_type' in data and data['_type'] == 'playlist':
            data = data['entries'][0]

        info = f'{data["title"]}'
        self.voice_manager.add_to_playlist(
            context,
            self.get_audiosource,
            [url],
        )

        if not self.voice_manager.is_playing(guild_id):
            await self.voice_manager.play_next(guild_id)
        else:
            await context.send(f'Added to playlist: {info}')

    async def get_audiosource(self, url: str) -> tuple[discord.FFmpegPCMAudio, str]:
        audio_source = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        infos = f'{audio_source.data["title"]}'
        return audio_source, infos
