import discord, json

from os import environ

TOKEN = None
with open('token.txt', encoding="utf-8") as f:
    TOKEN = f.read()
    f.close()


class DabloonBot(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')


intents = discord.Intents.default()
intents.message_content = True

client = DabloonBot(intents=intents)
client.run(TOKEN)
