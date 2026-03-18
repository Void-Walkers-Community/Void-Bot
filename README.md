<div align="center">

# 🌌 VOID-BOT
**The Central Nervous System for the VoidWalkers CTF Team**

[![Python 3.14+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
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

### 🟢 Phase 1: Operations (Current Focus)
- [x] **Modular Architecture:** Cog-based system for infinite scalability.
- [ ] **CTF Event Creation:** Admin commands to generate CTF dashboards with Start/End times, Team Size, and CTFTime links.
- [ ] **Role Assignment UI:** Interactive buttons for players to mark `⭐ Interested` or `🧭 Apply for Captain`.
- [ ] **Automated Deployment:** Bot automatically DMs team credentials or invite links to selected rosters.
- [ ] **Zero-Hour Alerts:** Background workers that ping players and send DMs exactly when a CTF goes live.

### 🟡 Phase 2: Gamification (Next Up)
- [ ] **Dynamic Leaderboards:** Tracks engagement points internally across events.
- [ ] **Leveling System:** Gain EXP and level up as you participate and solve challenges.
- [ ] **Internal Flagging:** Share challenge names and submit internal flags to the bot to prove solves and gain points.
- [ ] **Clock-in / Clock-out:** Session tracking to monitor active hours during a 48hr CTF.

### 🔴 Phase 3: Analytics (Future)
- [ ] **Hacker Profile Cards:** Generate a dynamic image/text card showing a player's EXP, solves, CTFs participated in, and captain roles.

---

## 💻 Deployment Guide

Void-Bot is designed to be hosted on a secure Linux environment (but it can still be run on Windows and MacOS). Follow these steps to deploy the bot to your system.

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
*(Note: Arch includes the `venv` module in the base `python` package).*

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
Once the prerequisites are installed, clone the bot to your local machine or server.
```bash
git clone https://github.com/Void-Walkers-Community/Void-Bot
cd void-bot
```
---

### 3. Setup the Virtual Environment
We strongly recommend using a virtual environment to isolate the bot's dependencies from your system's Python packages.

**Linux / macOS**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

*(Note: If `requirements.txt` is missing, you can manually install the required packages by running: `pip install discord.py aiosqlite python-dotenv`)*

---

### 4. Configuration & Secrets (.env)
**CRITICAL:** Never commit your bot token to GitHub. Void-Bot uses a `.env` file to securely load credentials.

1. In the root `void-bot` directory, create a file named `.env`:
   - **Linux/macOS:** `nano .env`
2. Add the following lines to the file, replacing the placeholder with your actual Discord Bot Token:
```ini
TOKEN=your_super_secret_discord_bot_token_here
APPLICATION_CHANNEL_ID=Channel_ID
PROOF_LOG_CHANNEL_ID=Channel_ID
AUDIT_LOG_CHANNEL_ID=Channel_ID
```
3. Save and close the file. Make sure `.env` is listed in your `.gitignore` file.

---

### 5. Booting the System
With the environment activated and the `.env` configured, you are ready to bring the bot online.
```bash
# On Linux/macOS
python3 main.py
```
If successful, the terminal will output that the bot is operational and connected to Discord.
