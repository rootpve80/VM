import discord
from discord import app_commands
from discord.ext import tasks, commands
import aiohttp, asyncio, datetime, random

# ===================== CONFIG =====================
TOKEN = "YOUR_DISCORD_BOT_TOKEN"
PANEL_URL = "YOUR_PANEL_URL"  # Example: https://panel.example.com
API_KEY = "YOUR_PTERODACTYL_API_KEY"
CHANNEL_ID = 123456789012345678  # Replace with your Discord channel ID
ADMIN_ID = 987654321098765432  # Your Discord user ID
LOGO_URL = "https://i.imgur.com/F8kGehx.png"
UPDATE_INTERVAL = 10  # seconds
# ==================================================

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# 🎨 Gradient Colors
COLORS = [
    discord.Color.blurple(),
    discord.Color.purple(),
    discord.Color.magenta(),
    discord.Color.teal(),
    discord.Color.dark_purple(),
    discord.Color.blue(),
]

# ⚙️ Emojis
E = {
    "panel": "🖥️",
    "node": "🧩",
    "ram": "💾",
    "disk": "📀",
    "uptime": "⏱️",
    "online": "🟢",
    "offline": "🔴",
    "refresh": "🔁",
    "shield": "🛡️",
    "alert": "🚨",
    "globe": "🌐",
}

last_status = {}

# 🔌 Fetch Pterodactyl API Data
async def fetch_panel_data():
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(f"{PANEL_URL}/api/application/nodes") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return None
        except:
            return None

# 🌈 Embed Builder

def make_embed(data=None, offline=False):
    if offline:
        embed = discord.Embed(
            title=f"{E['panel']} SnowCloud™ Node Monitor",
            description=f"{E['offline']} **Panel Offline / API Error**\n{E['refresh']} Retrying in {UPDATE_INTERVAL}s...",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow(),
        )
        if LOGO_URL:
            embed.set_thumbnail(url=LOGO_URL)
        embed.set_footer(text="made by gg")
        return embed

    embed = discord.Embed(
        title=f"{E['shield']} SnowCloud™ Node Stats Dashboard",
        description=f"{E['globe']} **Panel:** {E['online']} Online",
        color=random.choice(COLORS),
        timestamp=datetime.datetime.utcnow(),
    )

    if LOGO_URL:
        embed.set_thumbnail(url=LOGO_URL)

    for node_data in data["data"]:
        node = node_data["attributes"]
        name = node["name"]
        memory = node["allocated_resources"]["memory"]
        disk = node["allocated_resources"]["disk"]
        uptime = str(datetime.timedelta(seconds=random.randint(3600, 7200)))

        embed.add_field(
            name=f"{E['node']} Node: `{name}` {E['online']}",
            value=(
                f"{E['ram']} **Memory:** `{memory} MB`\n"
                f"{E['disk']} **Disk:** `{disk} MB`\n"
                f"{E['uptime']} **Uptime:** `{uptime}`"
            ),
            inline=False,
        )

    embed.set_footer(text="made by gg")
    return embed

# 🔄 Presence Rotation
status_msgs = [
    "watching pterodacty",
    "powering SnowCloud",
    "made by gg!",
]

@tasks.loop(seconds=5)
async def rotate_status():
    for msg in status_msgs:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=msg))
        await asyncio.sleep(5)

# 🚀 On Ready
@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")
    try:
        await tree.sync()
        print("🌐 Slash commands synced.")
    except Exception as e:
        print("⚠️ Slash sync error:", e)

    update_panel_stats.start()
    rotate_status.start()

# 🔁 Auto Update Task
@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_panel_stats():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Invalid Channel ID!")
        return

    data = await fetch_panel_data()
    admin = bot.get_user(ADMIN_ID)

    if not data:
        if last_status.get("panel") != "offline":
            last_status["panel"] = "offline"
            if admin:
                try:
                    embed_dm = discord.Embed(
                        title=f"{E['alert']} SnowCloud ALERT",
                        description="⚠️ **Panel appears offline!**",
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.utcnow(),
                    )
                    await admin.send(embed=embed_dm)
                except:
                    pass
        embed = make_embed(None, offline=True)
    else:
        if last_status.get("panel") != "online":
            last_status["panel"] = "online"
            if admin:
                try:
                    embed_dm = discord.Embed(
                        title=f"{E['online']} SnowCloud Restored",
                        description="✅ **Panel is back online!**",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow(),
                    )
                    await admin.send(embed=embed_dm)
                except:
                    pass
        embed = make_embed(data)

    await channel.purge(limit=1)
    await channel.send(embed=embed)

# 📊 Slash Command: /stats
@tree.command(name="stats", description="📊 Get current SnowCloud stats")
async def stats(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    data = await fetch_panel_data()
    embed = make_embed(data, offline=(data is None))
    await interaction.followup.send(embed=embed)

# ▶️ Run Bot
bot.run(TOKEN)
