import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} conectado com sucesso!")

    try:
        await bot.load_extension("cogs.painel")
        print("✅ Cog painel carregada.")
    except Exception as e:
        print(f"❌ Erro ao carregar cog: {e}")


bot.run(TOKEN)