import time

import discord
from discord.ext import commands
import os
from config import TOKEN
from database import DB, setup_database


class VoidBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await setup_database()

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"Loaded Cog: {filename}")
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")

        # re-register persistent EventViews so buttons survive restarts
        import aiosqlite
        from cogs.events import EventView

        now = int(time.time())
        async with aiosqlite.connect(DB) as db:
            cursor = await db.execute("SELECT id, name, start_ts, end_ts FROM events WHERE end_ts >= ?", (now,))
            for row in await cursor.fetchall():
                self.add_view(EventView(*row))

        await self.tree.sync()
        print("Slash commands synced.")

    async def on_ready(self):
        print(f"{self.user} is online and fully operational!")


bot = VoidBot()

if __name__ == "__main__":
    bot.run(TOKEN)