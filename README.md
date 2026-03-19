<div align="center">

# 🌌 VOID-BOT
**The Central Nervous System for the VoidWalkers CTF Team**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord-py-5865F2.svg)](https://github.com/Rapptz/discord.py)
[![Database](https://img.shields.io/badge/sqlite-aiosqlite-lightgrey.svg)](https://sqlite.org/index.html)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)

> An advanced Discord bot designed to automate CTF operations, track team engagement, and gamify the hacking experience.

---
</div>

## ⚙️ Core Architecture
Void-Bot is built from the ground up to be lightweight, secure, and modular. Running on a hardened homelab, it utilizes an asynchronous **Discord.py Cog architecture** to ensure commands, background tasks, and database queries run concurrently without blocking.

## 🚩 Features & Roadmap

Our development is tracked via the internal GitHub Project board. Here is the current state of the Bot's arsenal:

### 🟢 Phase 1: Operations
- [x] **Modular Architecture:** Cog-based system with `CoreCog`, `EventsCog`, `DashboardCog`, and `GamificationCog`.
- [x] **CTF Event Creation:** Admin commands to generate CTF event embeds with start/end times, team size, and CTFTime links.
- [x] **Role Assignment UI:** Persistent interactive buttons for players to mark `⭐ Interested`, `🧭 Apply for Captain`, or `❌ Withdraw`.
- [x] **Automated Deployment:** Bot automatically DMs team credentials or invite links to selected rosters.
- [x] **Zero-Hour Alerts:** Background task that DMs selected players exactly when a CTF goes live.
- [x] **Live Dashboard:** Auto-updating embed that displays all upcoming and active CTFs with live registration counts.
- [x] **Clock-in / Clock-out:** Session tracking to monitor active hours during a CTF event.
- [x] **Idle Flagger:** Players are auto-clocked out if no proof is submitted within 70 minutes.

### 🟡 Phase 2: Gamification (Current Focus)
- [x] **Proof Submission:** Players upload screenshots of their progress via `/proof`, re-hosted to a permanent staff channel.
- [ ] **Leaderboards:** Rankings by active time and proof count per event.
- [ ] **Internal Flagging:** Share challenge names and submit flags to the bot to prove solves and earn points.
- [ ] **Leveling System:** Gain EXP and level up as you participate and solve challenges.

### 🔴 Phase 3: Analytics (Future)
- [ ] **Engagement Tracker:** Admin analytics per event showing participation rates and challenge category breakdowns.
- [ ] **Hacker Profile Cards:** A dynamic text card showing a player's EXP, solves, CTFs participated in, and captain history.

---

## 💻 Deployment Guide

Void-Bot is designed to be hosted on a secure Linux environment (but it can still be run on Windows and macOS). Follow these steps to deploy the bot to your system.

### 1. Prerequisites
Ensure your system has **Python 3.10+** and **Git** installed. Select your operating system or distribution below:

**Debian / Ubuntu**
```bash
sudo apt update && sudo apt install python3 python3-venv python3-pip git
```

**Arch Linux**
```bash
sudo pacman -Syu python python-pip git
```
*(Note: Arch includes the `venv` module in the base `python` package.)*

**Fedora / RHEL**
```bash
sudo dnf install python3 python3-pip git
```

**macOS (via Homebrew)**
```bash
brew install python git
```

---

### 2. Clone the Repository
```bash
git clone https://github.com/Void-Walkers-Community/Void-Bot
cd Void-Bot
```

---

### 3. Setup the Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 4. Configuration & Secrets (.env)
**CRITICAL:** Never commit your bot token to GitHub. Void-Bot uses a `.env` file to securely load all credentials and channel IDs.

Copy the example file and fill in your values:
```bash
cp .env.example .env
nano .env
```
```ini
# Bot token from the Discord Developer Portal
TOKEN=your_bot_token_here

# Channel where Interested / Captain applications are posted
APPLICATION_CHANNEL_ID=000000000000000000

# Hidden staff channel where proof screenshots are permanently stored
PROOF_LOG_CHANNEL_ID=000000000000000000

# Staff-only channel that receives all admin audit logs
AUDIT_LOG_CHANNEL_ID=000000000000000000
```

The bot will **refuse to start** if any of these values are missing.

---

### 5. Booting the System
```bash
python3 main.py
```

If successful, the terminal will confirm all Cogs loaded and slash commands synced.
```
Loaded cogs.core
Loaded cogs.events
Loaded cogs.dashboard
Loaded cogs.gamification
Slash commands synced.
VoidBot#1234 is online and fully operational!
```
