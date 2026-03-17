import discord
from discord.ext import commands
from discord import app_commands

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check if the bot is alive")
    async def ping(self, interaction: discord.Interaction):
        # Calculate latency
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"VoidWalkers bot operational \nLatency: `{latency}ms`")

async def setup(bot):
    await bot.add_cog(Core(bot))
