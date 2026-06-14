import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} conectado!")

    try:
        await bot.load_extension("cogs.painel")
        await bot.tree.sync()
        print("✅ Comandos sincronizados.")
    except Exception as e:
        print(f"❌ Erro: {e}")


bot.run(TOKEN)