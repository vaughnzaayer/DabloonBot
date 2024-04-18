import discord
from os import environ
from dotenv import load_dotenv
from discord import app_commands
from discord.client import _log

import monies

BOUNTIES_DATA = "data/bounties.json"
USER_DATA = "data/users.json"

load_dotenv()

TOKEN = environ["DISCORD_TOKEN"]
ONE_MONIES_EMOJI_NAME = environ["ONE_MONIES_EMOJI"]
FIVE_MONIES_EMOJI_NAME = environ["FIVE_MONIES_EMOJI"]
TEN_MONIES_EMOJI_NAME = environ["TEN_MONIES_EMOJI"]
