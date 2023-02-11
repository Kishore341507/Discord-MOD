import discord
import json
import os
import asyncio
from discord.ext import commands
from botmain import client
import re
from dotenv import load_dotenv

load_dotenv()

@client.event
async def on_ready():
    print(f'bot logged in named : {client.user}')


@client.command()
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def ping(ctx):
    ping = round(client.latency * 1000 , ndigits=2)
    await ctx.reply(f'pong! `{ping}ms`')

async def load():

    for filename in os.listdir('./commands'):
        if filename.endswith('.py'):
            await client.load_extension( f'commands.{filename[:-3]}')
        elif not filename.endswith('.py'):
            filenametemp =  filename
            for filename in os.listdir(f'./commands/{filenametemp}'):
                if filename.endswith('.py'):
                   await client.load_extension(f'commands.{filenametemp}.{filename[:-3]}')
                             
asyncio.run(load())
client.run(os.getenv('TOKEN'))
