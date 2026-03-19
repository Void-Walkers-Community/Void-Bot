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
        self.withdraw_button.custom_id   = f"withdraw_{event_id}"

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

    @discord.ui.button(label="❌ Withdraw", style=discord.ButtonStyle.red, custom_id="withdraw_placeholder")
    async def withdraw_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if int(time.time()) > self.start_ts:
            await interaction.response.send_message("❌ Registration is closed, event has already started.", ephemeral=True)
            return

        async with get_db() as db:
            cur = await db.execute("SELECT role FROM event_users WHERE event_id=? AND user_id=?", (self.event_id, interaction.user.id))
            existing = await cur.fetchone()
            if not existing:
                await interaction.response.send_message("You are not registered for this event.", ephemeral=True)
                return

            await db.execute("DELETE FROM event_users WHERE event_id=? AND user_id=?", (self.event_id, interaction.user.id))
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

        await interaction.response.send_message("✅ Registration withdrawn.", ephemeral=True)
        await interaction.message.edit(embed=embed)

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

        now = int(time.time())
        if start_ts < now:
            await interaction.response.send_message("❌ Start time cannot be in the past.", ephemeral=True)
            return
        if end_ts <= start_ts:
            await interaction.response.send_message("❌ End time must be after start time.", ephemeral=True)
            return
        if team_size < 0:
            await interaction.response.send_message("❌ Team size cannot be negative.", ephemeral=True)
            return

        start_display = datetime.fromtimestamp(start_ts).strftime("%b %d, %Y %I:%M %p")
        end_display   = datetime.fromtimestamp(end_ts).strftime("%b %d, %Y %I:%M %p")

        async with get_db() as db:
            cur = await db.execute(
                "INSERT INTO events(name,start_time,end_time,start_ts,end_ts,team_size,ctftime_link,channel_id) VALUES (?,?,?,?,?,?,?,?)",
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


    @app_commands.command(name="manage_event", description="Send event access details to players")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        mode="Choose how players will join the event",
        event_id="Select the event",
        event_name="Name of the event",
        captain="Captain of the team",
        players="Mention players separated by space",
        team_name="Team name (for credential mode)",
        team_password="Team password (for credential mode)",
        invite_link="Invite link (for invite mode)"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="Team Credentials", value="team"),
        app_commands.Choice(name="Invite Link", value="invite")
    ])
    async def manage_event(
        self,
        interaction: discord.Interaction,
        mode: str,
        event_id: int,
        captain: discord.Member,
        players: str,
        team_name: str = None,
        event_name: str = None,
        team_password: str = None,
        invite_link: str = None
    ):
        if mode == "team" and not (team_name and team_password):
            await interaction.response.send_message("❌ Credential mode requires both `team_name` and `team_password`.", ephemeral=True)
            return
        if mode == "invite" and not invite_link:
            await interaction.response.send_message("❌ Invite mode requires an `invite_link`.", ephemeral=True)
            return

        user_ids = [int(uid) for uid in SNOWFLAKE_RE.findall(players)]
        if not user_ids:
            await interaction.response.send_message("❌ No valid Discord mentions found in `players`.", ephemeral=True)
            return

        await interaction.response.send_message("Sending team information...", ephemeral=True)

        success = failed = 0
        async with get_db() as db:
            for uid in user_ids:
                member = interaction.guild.get_member(uid)
                if not member:
                    failed += 1
                    continue
                try:
                    if mode == "team":
                        embed = discord.Embed(title="⚔️ CTF Team Assignment", color=0x00ffcc)
                        embed.add_field(name="Event", value=event_name or str(event_id), inline=False)
                        embed.add_field(name="Team Name", value=team_name, inline=False)
                        embed.add_field(name="Team Password", value=f"||{team_password}||", inline=False)
                        embed.add_field(name="Captain", value=captain.mention, inline=False)
                    else:
                        embed = discord.Embed(title="⚔️ CTF Event Invitation", color=0x00ffcc)
                        embed.add_field(name="Event", value=event_name or str(event_id), inline=False)
                        embed.add_field(name="Invite Link", value=invite_link, inline=False)
                        embed.add_field(name="Captain", value=captain.mention, inline=False)

                    await member.send(embed=embed)
                    await db.execute("INSERT OR IGNORE INTO event_selected(event_id, user_id) VALUES (?,?)", (event_id, uid))
                    success += 1
                except discord.Forbidden:
                    log.warning("Can't DM %s — DMs are closed", uid)
                    failed += 1
                except Exception as e:
                    log.error("DM to %s failed: %s", uid, e)
                    failed += 1
            await db.commit()

        await interaction.followup.send(f"✅ Sent to {success} players\n❌ Failed: {failed}", ephemeral=True)
        self.bot.dispatch(
            "audit_log", "DEPLOY_CREDENTIALS", interaction.user,
            f"Mode: `{mode}` · Event ID: `{event_id}` · Captain: {captain.mention} · "
            f"Sent: {success} · Failed: {failed}"
        )

    @manage_event.autocomplete("event_id")
    async def manage_event_autocomplete(self, interaction: discord.Interaction, current: str):
        now = int(time.time())
        async with get_db() as db:
            cur = await db.execute("SELECT id, name FROM events WHERE end_ts >= ? ORDER BY start_ts DESC", (now,))
            rows = await cur.fetchall()
        return [
            app_commands.Choice(name=f"{r['name']} (ID: {r['id']})", value=r["id"])
            for r in rows if current.lower() in r["name"].lower()
        ][:25]

    @manage_event.error
    async def manage_event_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)

    @app_commands.command(name="edit_event", description="Edit a CTF event")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        event_id="Select the event to edit",
        name="New name",
        start_time="New start time e.g. 3/21/26, 6:00 PM",
        end_time="New end time e.g. 3/22/26, 6:00 PM",
        team_size="New team size (0 = unlimited)",
        ctftime_link="New CTFTime link"
    )
    async def edit_event(
        self,
        interaction: discord.Interaction,
        event_id: int,
        name: str = None,
        start_time: str = None,
        end_time: str = None,
        team_size: int = None,
        ctftime_link: str = None
    ):
        if ctftime_link and not CTFTIME_RE.match(ctftime_link):
            await interaction.response.send_message("❌ CTFTime link must start with `https://ctftime.org/`.", ephemeral=True)
            return

        async with get_db() as db:
            cur = await db.execute("SELECT name, start_time, end_time, start_ts, end_ts, team_size, ctftime_link FROM events WHERE id=?", (event_id,))
            row = await cur.fetchone()
            if not row:
                await interaction.response.send_message("❌ Event not found.", ephemeral=True)
                return

            new_name      = name or row["name"]
            new_team_size = team_size if team_size is not None else row["team_size"]
            new_ctftime   = ctftime_link or row["ctftime_link"]

            if new_team_size < 0:
                await interaction.response.send_message("❌ Team size cannot be negative.", ephemeral=True)
                return

            try:
                new_start_ts   = parse_time(start_time) if start_time else row["start_ts"]
                new_start_time = start_time or row["start_time"]
            except ValueError as e:
                await interaction.response.send_message(f"❌ {e}", ephemeral=True)
                return

            try:
                new_end_ts   = parse_time(end_time) if end_time else row["end_ts"]
                new_end_time = end_time or row["end_time"]
            except ValueError as e:
                await interaction.response.send_message(f"❌ {e}", ephemeral=True)
                return

            if new_end_ts <= new_start_ts:
                await interaction.response.send_message("❌ End time must be after start time.", ephemeral=True)
                return

            await db.execute(
                "UPDATE events SET name=?, start_time=?, end_time=?, start_ts=?, end_ts=?, team_size=?, ctftime_link=? WHERE id=?",
                (new_name, new_start_time, new_end_time, new_start_ts, new_end_ts, new_team_size, new_ctftime, event_id)
            )
            await db.commit()

        await interaction.response.send_message(f"✅ Event **{new_name}** updated successfully!", ephemeral=True)
        self.bot.dispatch("audit_log", "EDIT_EVENT", interaction.user, f"Updated **{new_name}** (ID: `{event_id}`)")

        self.bot.dispatch("dashboard_refresh")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))