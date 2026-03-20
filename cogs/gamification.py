import logging
import time

import discord
from discord import app_commands
from discord.ext import commands, tasks

from database import get_db

log = logging.getLogger(__name__)


async def _upsert_minutes(db, user_id, event_id, minutes):
    cur = await db.execute("SELECT 1 FROM player_stats WHERE user_id=? AND event_id=?", (user_id, event_id))
    if await cur.fetchone():
        await db.execute("UPDATE player_stats SET total_minutes=total_minutes+? WHERE user_id=? AND event_id=?", (minutes, user_id, event_id))
    else:
        await db.execute("INSERT INTO player_stats(user_id, event_id, total_minutes) VALUES (?,?,?)", (user_id, event_id, minutes))


class GamificationCog(commands.Cog, name="Gamification"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clockin", description="Clock in to start tracking your CTF activity")
    async def clockin(self, interaction: discord.Interaction):
        now = int(time.time())
        async with get_db() as db:
            cur = await db.execute("SELECT id, name FROM events WHERE start_ts <= ? AND end_ts >= ?", (now, now))
            event = await cur.fetchone()
            if not event:
                await interaction.response.send_message("❌ No active CTF event right now.", ephemeral=True)
                return

            event_id, event_name = event["id"], event["name"]

            cur = await db.execute(
                "SELECT 1 FROM event_selected WHERE event_id=? AND user_id=?",
                (event_id, interaction.user.id)
            )
            if not await cur.fetchone():
                await interaction.response.send_message("❌ You are not part of this event's team.", ephemeral=True)
                return

            cur = await db.execute("SELECT 1 FROM clock_sessions WHERE event_id=? AND user_id=? AND is_active=1", (event_id, interaction.user.id))
            if await cur.fetchone():
                await interaction.response.send_message("⚠️ You are already clocked in!", ephemeral=True)
                return

            await db.execute("INSERT INTO clock_sessions(event_id, user_id, clock_in_time, is_active) VALUES (?,?,?,1)", (event_id, interaction.user.id, now))
            await db.commit()

        await interaction.response.send_message(
            f"✅ Clocked in for **{event_name}**!\n"
            f"⏱️ You will be pinged every hour to submit proof.\n"
            f"Use `/proof` to submit screenshots of your progress.",
            ephemeral=True
        )

    @app_commands.command(name="clockout", description="Clock out to stop tracking your CTF activity")
    async def clockout(self, interaction: discord.Interaction):
        now = int(time.time())
        async with get_db() as db:
            cur = await db.execute("SELECT id, event_id, clock_in_time FROM clock_sessions WHERE user_id=? AND is_active=1", (interaction.user.id,))
            session = await cur.fetchone()
            if not session:
                await interaction.response.send_message("❌ You are not clocked in.", ephemeral=True)
                return

            session_id    = session["id"]
            event_id      = session["event_id"]
            clock_in_time = session["clock_in_time"]
            total_minutes = max(0, (now - clock_in_time) // 60)

            await db.execute("UPDATE clock_sessions SET clock_out_time=?, is_active=0 WHERE id=?", (now, session_id))
            await _upsert_minutes(db, interaction.user.id, event_id, total_minutes)
            await db.commit()

        hours, mins = divmod(total_minutes, 60)
        await interaction.response.send_message(f"✅ Clocked out!\n⏱️ Active time this session: **{hours}h {mins}m**", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GamificationCog(bot))