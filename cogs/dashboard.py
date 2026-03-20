import logging
import time

import discord
from discord import app_commands
from discord.ext import commands, tasks

from database import get_db

log = logging.getLogger(__name__)


async def build_dashboard_embed():
    now = int(time.time())

    async with get_db() as db:
        cur = await db.execute(
            """
            SELECT
                e.id, e.name, e.start_ts, e.end_ts, e.ctftime_link,
                COALESCE(SUM(CASE WHEN eu.role='interested' THEN 1 END), 0) AS interested,
                COALESCE(SUM(CASE WHEN eu.role='captain'    THEN 1 END), 0) AS captains,
                COALESCE(COUNT(DISTINCT es.user_id), 0) AS selected
            FROM events e
            LEFT JOIN event_users    eu ON e.id = eu.event_id
            LEFT JOIN event_selected es ON e.id = es.event_id
            WHERE e.end_ts >= ?
            GROUP BY e.id
            ORDER BY e.start_ts ASC
            """,
            (now,)
        )
        events = await cur.fetchall()

    embed = discord.Embed(title="VOID WALKERS CTF CONTROL PANEL", color=0x00ffcc)

    if not events:
        embed.description = "No upcoming events."
        return embed

    for e in events:
        start_ts, end_ts = e["start_ts"], e["end_ts"]
        if now < start_ts:
            status = "⏳ Upcoming"
        elif start_ts <= now <= end_ts:
            status = "🧿 Live"
        else:
            status = "✅ Ended"

        embed.add_field(
            name=f"{status} — {e['name']}",
            value=(
                f"Start: <t:{start_ts}:R>\nEnd: <t:{end_ts}:R>\n"
                f"[CTFTime]({e['ctftime_link']})\n"
                f"⭐ Interested: {e['interested']} | 🧭 Captains: {e['captains']} | ⚔️ Team: {e['selected']}"
            ),
            inline=False
        )

    return embed


async def refresh_dashboard(client):
    async with get_db() as db:
        cur = await db.execute("SELECT channel_id, message_id FROM dashboard_messages LIMIT 1")
        row = await cur.fetchone()
    if not row:
        return

    channel = client.get_channel(row["channel_id"])
    if not channel:
        return

    try:
        msg = await channel.fetch_message(row["message_id"])
        embed = await build_dashboard_embed()
        await msg.edit(embed=embed)
    except discord.NotFound:
        async with get_db() as db:
            await db.execute("DELETE FROM dashboard_messages WHERE channel_id=?", (row["channel_id"],))
            await db.commit()
        log.warning("Dashboard message was deleted externally, cleared from DB")
    except discord.HTTPException as e:
        log.error("Dashboard refresh failed: %s", e)


class DashboardCog(commands.Cog, name="Dashboard"):
    def __init__(self, bot):
        self.bot = bot
        self.dashboard_updater.start()

    def cog_unload(self):
        self.dashboard_updater.cancel()

    @commands.Cog.listener()
    async def on_dashboard_refresh(self):
        await refresh_dashboard(self.bot)

    @tasks.loop(minutes=5)
    async def dashboard_updater(self):
        await refresh_dashboard(self.bot)

    @dashboard_updater.before_loop
    async def before_updater(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="dashboard", description="Show all scheduled CTF events")
    async def dashboard(self, interaction: discord.Interaction):
        embed = await build_dashboard_embed()
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        async with get_db() as db:
            await db.execute("INSERT OR REPLACE INTO dashboard_messages(channel_id, message_id) VALUES (?,?)", (interaction.channel.id, message.id))
            await db.commit()


async def setup(bot):
    await bot.add_cog(DashboardCog(bot))