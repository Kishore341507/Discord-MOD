import discord
from discord.ext import commands
import asyncpg
import os
import socket


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)
        
        self.db = await asyncpg.create_pool(dsn= os.getenv('DATABASE').replace("ip", f"{IP}") )
        print("Connection to db DONE!")



intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = MyBot( command_prefix = commands.when_mentioned_or("?") , strip_after_prefix =True, case_insensitive=True, intents=intents )