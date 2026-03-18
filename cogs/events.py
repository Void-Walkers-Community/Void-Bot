import re
import time
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import APPLICATION_CHANNEL_ID
from database import get_db

SNOWFLAKE_RE = re.compile(r"\b\d{17,20}\b")

class EventView(discord.ui.View):
    def __init__(self, event_id, event_name, start_ts, end_ts):
        super().__init__(timeout=None)
        self.event_id   = event_id
        self.event_name = event_name
        self.start_ts   = start_ts
        self.end_ts     = end_ts
        self.interested_button.custom_id = f"interested_{event_id}"
        self.captain_button.custom_id    = f"captain_{event_id}"

    async def _handle_register(self, interaction, role):
        if int(time.time()) > self.start_ts:
            await interaction.response.send_message("❌ Registration is closed, event has already started.", ephemeral=True)
            return

        async with get_db() as db:
            cur = await db.execute("SELECT role FROM event_users WHERE event_id=? AND user_id=?", (self.event_id, interaction.user.id))
            existing = await cur.fetchone()
            if existing:
                await interaction.response.send_message(f"You are already registered as **{existing['role']}** for this event.", ephemeral=True)
                return

            await db.execute("INSERT INTO event_users(event_id, user_id, role) VALUES (?,?,?)", (self.event_id, interaction.user.id, role))
            await db.commit()

            cur = await db.execute("SELECT COUNT(*) FROM event_users WHERE event_id=? AND role='interested'", (self.event_id,))
            interested_count = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM event_users WHERE event_id=? AND role='captain'", (self.event_id,))
            captain_count = (await cur.fetchone())[0]

        embed = interaction.message.embeds[0]
        for i, field in enumerate(embed.fields):
            if field.name == "Interested Players":
                embed.set_field_at(i, name="Interested Players", value=str(interested_count), inline=False)
            elif field.name == "Captain Applications":
                embed.set_field_at(i, name="Captain Applications", value=str(captain_count), inline=False)

        label = "⭐ **Interested Player**" if role == "interested" else "🧭 **Captain Application**"
        reply = "✅ Registered successfully!" if role == "interested" else "✅ Registered as Captain!"
        await interaction.response.send_message(reply, ephemeral=True)
        await interaction.message.edit(embed=embed)

        apps_channel = interaction.client.get_channel(APPLICATION_CHANNEL_ID)
        if apps_channel:
            await apps_channel.send(f"{label}\nUser: {interaction.user.mention}\nEvent: {self.event_name}")

    @discord.ui.button(label="⭐ Interested", style=discord.ButtonStyle.green, custom_id="interested_placeholder")
    async def interested_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_register(interaction, "interested")

    @discord.ui.button(label="🧭 Apply Captain", style=discord.ButtonStyle.blurple, custom_id="captain_placeholder")
    async def captain_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_register(interaction, "captain")


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
            await interaction.response.send_message("❌ Invalid time format. Use: `15/3/26, 9:41 PM`", ephemeral=True)
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

        view = EventView(event_id, name, start_ts, end_ts)
        self.bot.add_view(view)

        embed = discord.Embed(title=f"⚔️ {name}", description="New CTF Event", color=0x00ffcc)
        embed.add_field(name="Start Time", value=f"{start_display} (<t:{start_ts}:R>)", inline=False)
        embed.add_field(name="End Time",   value=f"{end_display} (<t:{end_ts}:R>)",     inline=False)
        embed.add_field(name="Team Size",  value="Unlimited" if team_size == 0 else str(team_size), inline=True)
        embed.add_field(name="CTFTime",    value=ctftime_link,                          inline=False)
        embed.add_field(name="Discussion Channel", value=discussion_channel.mention,    inline=False)
        embed.add_field(name="Interested Players",  value="0", inline=False)
        embed.add_field(name="Captain Applications", value="0", inline=False)

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(EventsCog(bot))