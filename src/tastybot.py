import os

import discord
from discord.ext.commands import Cog, Bot, Context, command
from discord import Member


class TastyBot(Cog):
    """
    Basic commands and reaction.
    """
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member: Member):
        """
        Called when a member join a
        guild I am connected to.

        Sends a little welcoming message randomly choosen.
        """
        channel = member.guild.system_channel
        if channel is None and len(member.guild.text_channels) > 0:
            channel = member.guild.text_channels[0]

        if channel is None: # No text channels
            return

        WELCOME_MSG = os.getenv('WELCOME_MSG')
        msgs = WELCOME_MSG.split(SPLIT_TOKEN)
        msg_number = randint(0, len(msgs)-1)
        msg = msgs[msg_number]
        await channel.send(msg)

    @Cog.listener()
    async def on_ready(self):
        """
        Called when the tasty bot is ready.

        Print debug infos.
        """
        print(f'{self.bot.user} has connected to Discord!')

        for guild in self.bot.guilds:
            print(f'Connected to {guild.name}')
            members = '\n - '.join([member.name for member in guild.members])
            print(f'Guild Members:\n - {members}')

            channel = guild.system_channel
            if channel is not None and guild.name == 'Insane server':
                await channel.send('Heyo ! Be ready for some tasty musics !')

        activity = discord.Activity(type=discord.ActivityType.listening, name='some Tastycool songs')
        await self.bot.change_presence(activity=activity)

    @Cog.listener()
    async def on_member_join(member: Member):
        """
        Sends a little welcoming message
        randomly choosen.
        """
        channel = member.guild.system_channel
        if not channel and len(member.guild.text_channels) > 0:
            channel = member.guild.text_channels[0]

        if not channel:
            return  # No text channel

        WELCOME_MSG = os.getenv('WELCOME_MSG')
        msgs = WELCOME_MSG.split(SPLIT_TOKEN)
        msg_number = random.randrange(0, len(msgs))
        msg = msgs[msg_number]
        await channel.send(msg)

    @Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """
        Log 'on_message' errors.
        Raise the others.
        """
        with open('../err.log', 'a') as f:
            if event == 'on_message':
                f.write(f'Unhandled message: {args[0]}\n')
            else:
                raise

    @command(name='links')
    async def tastylinks(self, context: Context):
        """
        To get to know more about Tastycool.
        """
        FB_LINK = os.getenv('TASTY_FB')
        PRODUCT_LINK = os.getenv('TASTY_PRODUCT')
        YT_LINK = os.getenv('TASTY_YT')
        SPOTIFY_LINK = os.getenv('TASTY_SPOTIFY')
        DEEZER_LINK = os.getenv('TASTY_DEEZER')

        msg = 'Tasty links :\n'
        msg += f'\t- [Facebook link] <{FB_LINK}>\t\t-- all tasty news\n'
        msg += f'\t- [Official website] <{PRODUCT_LINK}>\t\t-- buy their products\n'
        msg += f'\t- [Youtube channel] <{YT_LINK}>\n'
        msg += f'\t- [Spotify] <{SPOTIFY_LINK}>\n'
        msg += f'\t- [Deezer] <{DEEZER_LINK}>'
        await context.send(msg)
