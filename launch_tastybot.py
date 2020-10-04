import os
from dotenv import load_dotenv

from discord.ext.commands import Bot

from tastybot import TastyBot
from tastylisten import TastyListen


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = '!'
SPLIT_TOKEN = '::'

bot = Bot(command_prefix=PREFIX)
bot.add_cog(TastyBot(bot))
bot.add_cog(TastyListen(bot))
bot.run(TOKEN)
