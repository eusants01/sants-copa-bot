import os
import discord

from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

from cogs.services.copa_service import CopaService


CANAL_COPA_ID = int(os.getenv("CANAL_COPA_ID", 0))
MENSAGEM_COPA_ID = int(os.getenv("MENSAGEM_COPA_ID", 0))
CANAL_PALPITES_ID = int(os.getenv("CANAL_PALPITES_ID", 0))
BANNER_COPA_URL = os.getenv("BANNER_COPA_URL")


def agora():
    return datetime.now().strftime("%d/%m/%Y às %H:%M")


class PainelCopa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.atualizar_painel.start()

    def cog_unload(self):
        self.atualizar_painel.cancel()

    def criar_embed(self):
        dados = CopaService.carregar()

        embed = discord.Embed(
            title="🏆 SANTS COPA 2026",
            description="Central oficial da Copa do Mundo no servidor.",
            color=discord.Color.gold()
        )

        if BANNER_COPA_URL:
            embed.set_image(url=BANNER_COPA_URL)

        embed.add_field(
            name="🔥 Destaque",
            value=dados.get("destaque") or "Nenhum destaque cadastrado.",
            inline=False
        )

        embed.add_field(
            name="⚽ Jogos de Hoje",
            value="\n".join(dados.get("jogos_hoje", [])) or "Nenhum jogo cadastrado.",
            inline=False
        )

        embed.add_field(
            name="⏳ Próximos Jogos",
            value="\n".join(dados.get("proximos_jogos", [])) or "Nenhum próximo jogo cadastrado.",
            inline=False
        )

        embed.add_field(
            name="🎯 Palpites",
            value=f"Canal: <#{CANAL_PALPITES_ID}>" if CANAL_PALPITES_ID else "Canal de palpites não configurado.",
            inline=False
        )

        embed.add_field(
            name="🥇 Ranking",
            value="\n".join(dados.get("ranking", [])) or "Ranking ainda vazio.",
            inline=False
        )

        embed.set_footer(text=f"Última atualização • {agora()} • Sants Copa")

        return embed

    @app_commands.command(name="painel_copa", description="Cria o painel oficial da Sants Copa.")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_copa(self, interaction: discord.Interaction):
        painel = await interaction.channel.send(embed=self.criar_embed())

        await interaction.response.send_message(
            f"✅ Painel criado!\n\nMENSAGEM_COPA_ID:\n`{painel.id}`",
            ephemeral=True
        )

    @tasks.loop(minutes=10)
    async def atualizar_painel(self):
        await self.bot.wait_until_ready()

        if not CANAL_COPA_ID or not MENSAGEM_COPA_ID:
            return

        canal = self.bot.get_channel(CANAL_COPA_ID)
        if not canal:
            return

        try:
            mensagem = await canal.fetch_message(MENSAGEM_COPA_ID)
            await mensagem.edit(embed=self.criar_embed())
            print("✅ Painel atualizado.")
        except Exception as erro:
            print(f"❌ Erro ao atualizar painel: {erro}")


async def setup(bot):
    await bot.add_cog(PainelCopa(bot))