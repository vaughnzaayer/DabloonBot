import string

import discord
import json
import os
import dabloons
import enum

from os import environ
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

import dabloons

BOUNTIES_DATA = "data/bounties.json"
USER_DATA = "data/users.json"

load_dotenv()


class DabloonBot(discord.Client):

    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.synced = False

    async def on_ready(self):
        await tree.sync()
        self.synced = True
        print(f'Logged in as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        print(f'Author ID: {message.author.id}')


TOKEN = environ["DISCORD_TOKEN"]

client = DabloonBot()
tree = app_commands.CommandTree(client)

# Data Store
Users: {discord.User.id: dabloons.DabloonUser} = {}
Bounties: {str: dabloons.DabloonBounty} = {}


# Helpers
async def get_all_users(interaction: discord.Interaction):
    members = []
    async for member in interaction.guild.fetch_members():
        members.append(member)
    return members


@tree.command(name='add_dabloon_user', description='Adds a new user to the dabloon bank')
async def add_dabloon_user(interaction: discord.Interaction, user: discord.User):
    members = await get_all_users(interaction)
    if user not in members:
        await interaction.response.send_message(f'Invalid User')
        return

    if user.id in Users:
        await interaction.response.send_message(f'User {user} already exists within the database.')
    else:
        Users[user.id] = dabloons.DabloonUser(user.id)
        await interaction.response.send_message(f'Added user {user} \n Users = {Users}')


@tree.command(name='add_new_bounty', description='Adds a new bounty')
async def add_new_bounty(interaction: discord.Interaction, title: str, reward_amount: int, claim_limit: int = 1):
    if title in Bounties:
        await interaction.response.send_message(f'This bounty already exists')
        return

    if interaction.user.id not in Users:
        await interaction.response.send_message(f'You need to be registered to post a bounty')
        return

    newBounty = dabloons.DabloonBounty(title, Users[interaction.user.id], reward_amount, claim_limit)
    Bounties[title] = newBounty
    await interaction.response.send_message(f'Bounty registered')


async def claim_bounty_autocomplete(interaction: discord.Interaction, current: str) -> [app_commands.Choice[str]]:
    bounty_names = [name for name in Bounties]
    return [
        app_commands.Choice(name=bounty, value=bounty)
        for bounty in bounty_names if current.lower() in bounty.lower()
    ]


@tree.command(name='claim_bounty', description='Claim a bounty that is currently posted')
@app_commands.autocomplete(bounty=claim_bounty_autocomplete)
async def claim_bounty(interaction: discord.Interaction, bounty: str):
    await interaction.response.send_message('Done!')


@tree.context_menu(name='something_else')
async def some_func(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message('Got it!')




client.run(TOKEN)
