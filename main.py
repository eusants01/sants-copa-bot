import os
import asyncio
import discord

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} conectado com sucesso!")

    try:
        await bot.tree.sync()
        print("✅ Comandos slash sincronizados.")
    except Exception as erro:
        print(f"❌ Erro ao sincronizar comandos: {erro}")


async def load_extensions():
    extensoes = [
        "cogs.painel",
        "cogs.jogos"
    ]

    for extensao in extensoes:
        try:
            await bot.load_extension(extensao)
            print(f"✅ {extensao} carregado.")
        except Exception as erro:
            print(f"❌ Erro em {extensao}: {erro}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)


asyncio.run(main())