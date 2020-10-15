import os
import sys
from dotenv import load_dotenv

from discord.ext.commands import Bot

from src.tastybot import TastyBot
from src.tastylisten import TastyListen
from src.create_db import create_csv


if len(sys.argv) > 1:
    if '--help' in sys.argv or '-h' in sys.argv:
        print('Help for TastyBot:')
        print(f'\tpython3 {sys.argv[0]}: start the TastyBot')
        print(f'\tpython3 {sys.argv[0]} --init: create the database file')
        print(f'\tpython3 {sys.argv[0]} --help: print this help message')
        sys.exit(0)

    if '--init' == sys.argv[1] and len(sys.argv) == 2:
        create_csv('songs', 'songs.csv')
        print('DB created.')
        sys.exit(0)

    print('Error when parsing arguments.')
    print('Use --help.')
    sys.exit(1)


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = '!'
SPLIT_TOKEN = '::'

bot = Bot(command_prefix=PREFIX)
bot.add_cog(TastyBot(bot))
bot.add_cog(TastyListen(bot))
bot.run(TOKEN)
