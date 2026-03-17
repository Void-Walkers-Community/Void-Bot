import discord
from discord.ext import commands
import os
from config import TOKEN
from database import setup_database

class VoidBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Initialize database
        await setup_database()
        
        # Load all cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"Loaded Cog: {filename}")
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")
        
        # Sync slash commands to Discord
        await self.tree.sync()
        print("Slash commands synced.")

    async def on_ready(self):
        print(f"{self.user} is online and fully operational!")

bot = VoidBot()

if __name__ == "__main__":
    bot.run(TOKEN)
