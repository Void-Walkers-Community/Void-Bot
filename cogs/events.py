import time
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import APPLICATION_CHANNEL_ID
from database import get_db


class EventsCog(commands.Cog, name="Events"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="event_registration", description="Create a CTF event")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        name="Name of the CTF event",
        start_time='Start time — e.g. "15/3/26, 9:41 PM"',
        end_time='End time — e.g. "16/3/26, 9:41 PM"',
        team_size="Maximum players per team (0 = unlimited)",
        ctftime_link="Link to the event on CTFTime",
        discussion_channel="Channel where players will discuss the CTF"
    )
    async def event_registration(
        self,
        interaction: discord.Interaction,
        name: str,
        start_time: str,
        end_time: str,
        team_size: int,
        ctftime_link: str,
        discussion_channel: discord.TextChannel
    ):
        try:
            start_ts = int(datetime.strptime(start_time.strip(), "%d/%m/%y, %I:%M %p").timestamp())
            end_ts   = int(datetime.strptime(end_time.strip(),   "%d/%m/%y, %I:%M %p").timestamp())
        except ValueError:
            await interaction.response.send_message("❌ Invalid time format. Use: `3/15/26, 9:41 PM`", ephemeral=True)
            return

        start_display = datetime.fromtimestamp(start_ts).strftime("%b %d, %Y %I:%M %p")
        end_display   = datetime.fromtimestamp(end_ts).strftime("%b %d, %Y %I:%M %p")

        async with get_db() as db:
            cur = await db.execute(
                "INSERT INTO events(name,start_time,end_time,start_ts,end_ts,team_size,ctftime_link,channel_id) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (name, start_time, end_time, start_ts, end_ts, team_size, ctftime_link, discussion_channel.id)
            )
            event_id = cur.lastrowid
            await db.commit()

        embed = discord.Embed(title=f"⚔️ {name}", description="New CTF Event", color=0x00ffcc)
        embed.add_field(name="Start Time", value=f"{start_display} (<t:{start_ts}:R>)", inline=False)
        embed.add_field(name="End Time",   value=f"{end_display} (<t:{end_ts}:R>)",     inline=False)
        embed.add_field(name="Team Size",  value="Unlimited" if team_size == 0 else str(team_size), inline=True)
        embed.add_field(name="CTFTime",    value=ctftime_link,           inline=False)
        embed.add_field(name="Discussion Channel", value=discussion_channel.mention, inline=False)
        embed.add_field(name="Interested Players",  value="0", inline=False)
        embed.add_field(name="Captain Applications", value="0", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EventsCog(bot))