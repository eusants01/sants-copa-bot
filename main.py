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


class SantsCopaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        print("✅ Banco de dados conectado.")

        await self.load_extension("cogs.painel")
        print("✅ cogs.painel carregado.")

        await self.load_extension("cogs.palpites")
        print("✅ cogs.palpites carregado.")

        await self.load_extension("cogs.jogos")
        print("✅ cogs.jogos carregado.")

        guild = discord.Object(id=GUILD_ID)

        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)

        print(f"✅ {len(synced)} comandos slash sincronizados.")


bot = SantsCopaBot()


@bot.event
async def on_ready():
    print(f"✅ {bot.user} conectado com sucesso!")


async def main():
    async with bot:
        await bot.start(TOKEN)


asyncio.run(main())