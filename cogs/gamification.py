import io
import logging
import time

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import PROOF_LOG_CHANNEL_ID
from database import get_db

log = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 8 * 1024 * 1024


async def _upsert_minutes(db, user_id, event_id, minutes):
    cur = await db.execute("SELECT 1 FROM player_stats WHERE user_id=? AND event_id=?", (user_id, event_id))
    if await cur.fetchone():
        await db.execute("UPDATE player_stats SET total_minutes=total_minutes+? WHERE user_id=? AND event_id=?", (minutes, user_id, event_id))
    else:
        await db.execute("INSERT INTO player_stats(user_id, event_id, total_minutes) VALUES (?,?,?)", (user_id, event_id, minutes))


async def _upsert_proof(db, user_id, event_id):
    cur = await db.execute("SELECT 1 FROM player_stats WHERE user_id=? AND event_id=?", (user_id, event_id))
    if await cur.fetchone():
        await db.execute(
            "UPDATE player_stats SET proof_count=proof_count+1 WHERE user_id=? AND event_id=?", (user_id, event_id))
    else:
        await db.execute("INSERT INTO player_stats(user_id, event_id, proof_count) VALUES (?,?,1)", (user_id, event_id))


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

            cur = await db.execute("SELECT 1 FROM event_selected WHERE event_id=? AND user_id=?", (event_id, interaction.user.id))
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

    
    @app_commands.command(name="proof", description="Submit proof of your CTF activity")
    @app_commands.describe(
        challenge_type="Type of challenge you are working on",
        screenshot="Screenshot of your progress"
    )
    @app_commands.choices(challenge_type=[
        app_commands.Choice(name="Web",                 value="web"),
        app_commands.Choice(name="OSINT",               value="osint"),
        app_commands.Choice(name="Exploit/PWN",         value="exploit"),
        app_commands.Choice(name="Reverse Engineering", value="rev"),
        app_commands.Choice(name="Cryptography",        value="crypto"),
        app_commands.Choice(name="Other",               value="other")
    ])
    async def proof(
        self,
        interaction: discord.Interaction,
        challenge_type: str,
        screenshot: discord.Attachment
    ):
        if not (screenshot.content_type or "").startswith("image/"):
            await interaction.response.send_message("❌ Please upload an image file.", ephemeral=True)
            return

        if screenshot.size > MAX_IMAGE_SIZE:
            await interaction.response.send_message("❌ Image is too large (max 8 MB).", ephemeral=True)
            return

        now = int(time.time())
        await interaction.response.defer(ephemeral=True)

        async with get_db() as db:
            cur = await db.execute("SELECT id, event_id FROM clock_sessions WHERE user_id=? AND is_active=1", (interaction.user.id,))
            session = await cur.fetchone()
            if not session:
                await interaction.followup.send("❌ You are not clocked in. Use `/clockin` first.", ephemeral=True)
                return

            session_id = session["id"]
            event_id   = session["event_id"]

            cur = await db.execute("SELECT 1 FROM activity_proofs WHERE session_id=? AND submitted_at >= ?", (session_id, now - 3600))
            if await cur.fetchone():
                await interaction.followup.send("⚠️ You already submitted proof in the last hour. Wait for the next ping!", ephemeral=True)
                return

            await db.execute(
                "INSERT INTO activity_proofs"
                "(session_id, user_id, event_id, proof_url, challenge_type, submitted_at) "
                "VALUES (?,?,?,?,?,?)",
                (session_id, interaction.user.id, event_id, screenshot.url, challenge_type, now)
            )
            await _upsert_proof(db, interaction.user.id, event_id)
            await db.commit()

        proof_log_channel = self.bot.get_channel(PROOF_LOG_CHANNEL_ID)
        if proof_log_channel:
            try:
                async with aiohttp.ClientSession() as http:
                    async with http.get(screenshot.url) as resp:
                        resp.raise_for_status()
                        image_data = await resp.read()

                log_msg = await proof_log_channel.send(
                    f"📸 **Proof Log**\nUser: {interaction.user.mention}\n"
                    f"Challenge: **{challenge_type}**\nEvent ID: `{event_id}`",
                    file=discord.File(fp=io.BytesIO(image_data), filename=screenshot.filename)
                )
                permanent_url = log_msg.attachments[0].url

                async with get_db() as db:
                    await db.execute("UPDATE activity_proofs SET proof_url=? WHERE user_id=? AND event_id=? AND submitted_at=?", (permanent_url, interaction.user.id, event_id, now))
                    await db.commit()

            except aiohttp.ClientError as e:
                log.error("Failed to download proof image: %s", e)
            except discord.HTTPException as e:
                log.error("Failed to rehost proof: %s", e)

        await interaction.followup.send(
            f"✅ Proof submitted!\nChallenge type: **{challenge_type}**\n"
            f"Keep it up! Next proof in 1 hour. 🔥",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(GamificationCog(bot))