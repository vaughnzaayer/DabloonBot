import copy
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


async def claim_bounty_autocomplete(interaction: discord.Interaction, current: str) -> [app_commands.Choice[str]]:
    bounty_names = [name for name in Bounties]
    return [
        app_commands.Choice(name=bounty, value=bounty)
        for bounty in bounty_names if current.lower() in bounty.lower()
    ]


async def delete_bounty_autocomplete(interaction: discord.Interaction, current: str) -> [app_commands.Choice[str]]:
    bounty_author = interaction.user.id
    bounty_names = []
    for name in Bounties:
        if Bounties[name].author.id == bounty_author:
            bounty_names.append(name)
    return [
        app_commands.Choice(name=bounty, value=bounty)
        for bounty in bounty_names if current.lower() in bounty.lower()
    ]


async def message_bounty_author(interaction: discord.Interaction, bounty: dabloons.DabloonBounty,
                                request: dabloons.ClaimRequest):
    bountyAuthor = client.get_user(bounty.author.id)
    dm_channel = await client.create_dm(bountyAuthor)

    await dm_channel.send(f'**{client.get_user(request.claimee.id).display_name}** has sent you claim request '
                          f'on your bounty: *{bounty.title}*')


async def check_if_user(interaction: discord.Interaction):
    if interaction.user.id not in Users:
        return False
    return True


# Commands
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
@app_commands.describe(title='Name of the bounty')
@app_commands.describe(reward_amount='Number of dabloons awarded to a claimee')
@app_commands.describe(claim_limit='Number of times a user can claim the bounty (defaults to 1)')
@app_commands.describe(image='Any related media you would like to add to your bounty')
@app_commands.describe(description='Give a brief description of your bounty')
@app_commands.describe(total_claim_limit='The *total* number of times this bounty can be claimed')
@app_commands.describe(url='A url related to the bounty')
async def add_new_bounty(interaction: discord.Interaction, title: str, reward_amount: int, claim_limit: int = 1,
                         total_claim_limit: int = 1, image: discord.Attachment = None, description: str = None,
                         url: str = None):
    if title in Bounties:
        await interaction.response.send_message(f'This bounty already exists')
        return

    if interaction.user.id not in Users:
        await interaction.response.send_message(f'You need to be registered to post a bounty')
        return

    newBounty = dabloons.DabloonBounty(title=title, author=Users[interaction.user.id], rewardAmount=reward_amount,
                                       claimAmount=claim_limit, totalClaimAmount=total_claim_limit,
                                       image=image, description=description, url=url)
    Bounties[title] = newBounty
    await interaction.response.send_message(f'Bounty registered')


@tree.command(name='delete_bounty', description='Deletes a bounty you\'ve posted')
@app_commands.describe(title='Name of the bounty')
@app_commands.autocomplete(title=delete_bounty_autocomplete)
async def delete_bounty(interaction: discord.Interaction, title: str):
    if title not in Bounties:
        await interaction.response.send_message('That bounty does not exist')
        return

    if Bounties[title].author.id != interaction.user.id:
        await interaction.response.send_message('You can only delete your own bounties')
        return

    del Bounties[title]
    await interaction.response.send_message('Bounty successfully deleted')


@tree.command(name='claim_bounty', description='Claim a bounty that is currently posted')
@app_commands.autocomplete(bounty=claim_bounty_autocomplete)
async def claim_bounty(interaction: discord.Interaction, bounty: str):
    await interaction.response.defer()
    if bounty not in Bounties:
        await interaction.response.send_message('Please enter a valid bounty name')
        return

    target_bounty = Bounties[bounty]
    request = dabloons.ClaimRequest(claimee=Users[interaction.user.id])

    await message_bounty_author(interaction=interaction, bounty=target_bounty,
                                request=request)
    target_bounty.pendingClaims.append(request)

    await interaction.followup.send('Done!')


@tree.command(name='display_bounty', description='Display a bounty\'s information')
@app_commands.autocomplete(bounty=claim_bounty_autocomplete)
async def display_bounty(interaction: discord.Interaction, bounty: str):
    if bounty not in Bounties:
        await interaction.response.send_message('Please enter a valid bounty name')
        return

    embed = discord.Embed(title=Bounties[bounty].title, type='rich', description=None, colour=0xFF5733)
    embed.set_author(name=client.get_user(Bounties[bounty].author.id).display_name, url='',
                     icon_url=f'{client.get_user(Bounties[bounty].author.id).display_avatar}')

    if Bounties[bounty].image:
        embed.set_thumbnail(url=f'{Bounties[bounty].image}')

    if Bounties[bounty].description:
        embed.add_field(name='Description', value=f'{Bounties[bounty].description}', inline=False)

    embed.add_field(name='Reward', value=f'{Bounties[bounty].reward}', inline=True)

    if Bounties[bounty].url:
        embed.url = Bounties[bounty].url

    if Bounties[bounty].claimAmount:
        embed.add_field(name='Claim Amount', value=f'{Bounties[bounty].claimAmount}', inline=True)

    if Bounties[bounty].totalClaimAmount:
        embed.add_field(name='Global Claim Amount', value=f'{Bounties[bounty].totalClaimAmount}', inline=True)

    embed.set_footer(text=f'{Bounties[bounty].creationDate}')

    await interaction.response.send_message(embed=embed)


@tree.command(name='check_pending_bounty_requests', description='See the pending requests for your bounties')
async def check_pending_bounty_requests(interaction: discord.Interaction):
    if not await check_if_user(interaction=interaction):
        await interaction.response.send_message('You are not a Dabloon user')
        return

    userBountyClaims: {str: dabloons.DabloonBounty.pendingClaims} = {}
    for bounty in Bounties:
        if Bounties[bounty].author.id == interaction.user.id:
            userBountyClaims[bounty] = []
            for pending in Bounties[bounty].pendingClaims:
                userBountyClaims[bounty].append(client.get_user(pending.claimee.id).display_name)

    claimsEmbed = discord.Embed(title='Pending Bounty Claims')

    for claim in userBountyClaims:
        claimsEmbed.add_field(name=claim, value=f'Claims: {userBountyClaims[claim]}')

    await interaction.response.send_message(embed=claimsEmbed)


client.run(TOKEN)
