import os
import asyncio
import asyncpg
import discord

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
GUILD_ID = int(os.getenv("GUILD_ID"))

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
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)

        print(f"✅ {len(synced)} comandos slash sincronizados.")

    except Exception as e:
        print(e)


async def load_extensions():
    await bot.load_extension("cogs.painel")
    await bot.load_extension("cogs.palpites")
    await bot.load_extension("cogs.jogos")


async def main():
    async with bot:
        bot.pool = await asyncpg.create_pool(DATABASE_URL)

        print("✅ Banco de dados conectado.")

        await load_extensions()

        await bot.start(TOKEN)


asyncio.run(main())