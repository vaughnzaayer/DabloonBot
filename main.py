import copy
import string

import discord
import json
import os
import dabloons
import enum
import asyncio

from os import environ
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
import logging

from discord.client import _log

import dabloons

BOUNTIES_DATA = "data/bounties.json"
USER_DATA = "data/users.json"

load_dotenv()

TOKEN = environ["DISCORD_TOKEN"]
ONE_DABLOON_EMOJI_NAME = environ["ONE_DABLOON_EMOJI"]
FIVE_DABLOON_EMOJI_NAME = environ["FIVE_DABLOON_EMOJI"]
TEN_DABLOON_EMOJI_NAME = environ["TEN_DABLOON_EMOJI"]


# Views
class ConfirmBountyClaim(discord.ui.View):
    def __init__(self, claim: dabloons.ClaimRequest):
        super().__init__(timeout=None)
        self.value = None
        self.request = claim

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, custom_id="persistent_claim:confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirmed')
        self.value = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id="persistent_claim:decline")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Declined')
        self.value = False
        self.stop()


# Client
class DabloonBot(discord.Client):

    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.synced = False
        self.oneDabloonEmoji = None
        self.fiveDabloonEmoji = None
        self.tenDabloonEmoji = None
        self.emojiEnabledGuilds: {discord.Guild: {str: discord.Emoji.id}} = {}

        if ONE_DABLOON_EMOJI_NAME != "":
            self.oneDabloonEmoji = ONE_DABLOON_EMOJI_NAME
        if self.fiveDabloonEmoji != "":
            self.fiveDabloonEmoji = FIVE_DABLOON_EMOJI_NAME
        if self.tenDabloonEmoji != "":
            self.tenDabloonEmoji = TEN_DABLOON_EMOJI_NAME

        self.twitterLinks = ["https://twitter.com/", "https://x.com/"]

    async def validate_emojis(self):
        async for guild in self.fetch_guilds(limit=10):
            emojis: {str: discord.Emoji.id} = {}
            for emoji in await guild.fetch_emojis():
                emojis[emoji.name] = emoji.id
            emojisValid = True
            _log.info(f'Validating Emojis for {guild.name}.\nComplete Emoji List:{emojis}')

            if self.oneDabloonEmoji:
                if self.oneDabloonEmoji not in emojis:
                    _log.warning(f'Emoji Validation failed: {self.oneDabloonEmoji} is not in {guild.name}')
                    emojisValid = False
            if self.fiveDabloonEmoji:
                if self.fiveDabloonEmoji not in emojis:
                    _log.warning(f'Emoji Validation failed: {self.fiveDabloonEmoji} is not in {guild.name}')
                    emojisValid = False
            if self.tenDabloonEmoji:
                if self.tenDabloonEmoji not in emojis:
                    _log.warning(f'Emoji Validation failed: {self.tenDabloonEmoji} is not in {guild.name}')
                    emojisValid = False

            if emojisValid:
                _log.info(f'{guild.name} validated')
                self.emojiEnabledGuilds[guild] = {f'{ONE_DABLOON_EMOJI_NAME}': emojis[f'{ONE_DABLOON_EMOJI_NAME}'],
                                                  f'{FIVE_DABLOON_EMOJI_NAME}': emojis[f'{FIVE_DABLOON_EMOJI_NAME}'],
                                                  f'{TEN_DABLOON_EMOJI_NAME}': emojis[f'{TEN_DABLOON_EMOJI_NAME}']}

    async def on_ready(self):
        await self.validate_emojis()
        await tree.sync()
        self.synced = True
        print(f'Logged in as {self.user}!')

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        for link in self.twitterLinks:
            if link in message.content:
                active_channel = message.channel
                message_prefix = f"From <@{message.author.id}>: "
                new_message = message_prefix + message.content.replace(link, "https://fxtwitter.com/")
                await active_channel.send(new_message)
                await message.delete()
                break


    # async def setup_hook(self) -> None:
    #     self.add_view(ConfirmBountyClaim(claim=))


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
    claimeeUser = client.get_user(request.claimee.id)
    bountyAuthor = client.get_user(bounty.author.id)
    dm_channel = await client.create_dm(bountyAuthor)

    confirmEmbed = discord.Embed(title='Bounty Submission', colour=0xFFA500)
    confirmEmbed.set_author(name=f'{claimeeUser.display_name}', icon_url=claimeeUser.display_avatar, url='')
    confirmEmbed.add_field(name=f'{bounty.title}', value=f'{request.description}', inline=False)
    confirmView = ConfirmBountyClaim(request)

    await dm_channel.send(content=f'**{client.get_user(request.claimee.id).display_name}** has sent you claim request '
                                  f'on your bounty: *{bounty.title}*', view=confirmView, embed=confirmEmbed)

    _log.info('Interaction done')


async def check_if_user(user: discord.User):
    if user.id not in Users:
        return False
    return True


async def build_emoji_total(interaction: discord.Interaction, total: int):
    tens = total // 10
    total -= 10 * tens
    fives = total // 5
    total -= 5 * fives
    ones = total // 1

    tensStr = f'<:{TEN_DABLOON_EMOJI_NAME}:{client.emojiEnabledGuilds[interaction.guild][TEN_DABLOON_EMOJI_NAME]}>' \
              * tens
    fivesStr = f'<:{FIVE_DABLOON_EMOJI_NAME}:{client.emojiEnabledGuilds[interaction.guild][FIVE_DABLOON_EMOJI_NAME]}>' \
               * fives
    onesStr = f'<:{ONE_DABLOON_EMOJI_NAME}:{client.emojiEnabledGuilds[interaction.guild][ONE_DABLOON_EMOJI_NAME]}>' \
              * ones

    return tensStr + fivesStr + onesStr


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
async def claim_bounty(interaction: discord.Interaction, bounty: str, media1: discord.Attachment = None,
                       media2: discord.Attachment = None, media3: discord.Attachment = None,
                       media4: discord.Attachment = None, description: str = None):
    await interaction.response.defer()
    if bounty not in Bounties:
        await interaction.response.send_message('Please enter a valid bounty name')
        return

    target_bounty = Bounties[bounty]
    request = dabloons.ClaimRequest(claimee=Users[interaction.user.id],
                                    media=[media1, media2, media3, media4], description=description)

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


@tree.command(name='display_user', description='Displays the dabloon info of a user (defaults to self)')
async def display_user(interaction: discord.Interaction, user: discord.User):
    # await interaction.response.defer()
    members = await get_all_users(interaction)
    if user not in members:
        await interaction.response.send_message(f'Invalid User')
        return

    if not await check_if_user(user=user):
        await interaction.response.send_message(f'{user.display_name} is not a Dabloon user')
        return

    dabloonUser = Users[user.id]
    dabloonTotal = dabloonUser.dabloonCount

    userInfo = discord.Embed(title=f'{user.display_name}', colour=0x00FF00)
    userInfo.set_image(url=user.display_avatar)
    if interaction.guild in client.emojiEnabledGuilds:
        totalDisplay = await build_emoji_total(interaction=interaction, total=dabloonTotal)
        if len(totalDisplay) > 1024:
            userInfo.add_field(name='Dabloons', value=f'Total: {dabloonTotal}', inline=True)
        else:
            userInfo.add_field(name='Dabloons',
                               value=f'Total: {dabloonTotal}\n{await build_emoji_total(interaction=interaction, total=dabloonTotal)}',
                               inline=True)
    else:
        userInfo.add_field(name='Dabloons', value=f'Total: {dabloonTotal}', inline=True)

    await interaction.response.send_message(embed=userInfo)


@tree.command(name='set_dabloons', description='set dabloons')
async def set_dabloons(interaction: discord.Interaction, user: discord.User, amount: int):
    Users[user.id].dabloonCount = amount
    await interaction.response.send_message(f'Set {user}\'s dabloon total to {amount} dabloons')


client.run(TOKEN)
