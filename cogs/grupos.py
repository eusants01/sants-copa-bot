import discord

from discord.ext import commands
from discord import app_commands

from cogs.services.copa_service import CopaService


class Grupos(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(
        name="grupo",
        description="Visualiza um grupo da Copa."
    )

    @app_commands.describe(
        letra="Escolha a letra do grupo."
    )

    async def grupo(
        self,
        interaction: discord.Interaction,
        letra: str
    ):

        letra = letra.upper()

        dados = CopaService.carregar()

        grupos = dados.get(
            "grupos",
            {}
        )

        if letra not in grupos:

            await interaction.response.send_message(
                "❌ Grupo não encontrado.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title=f"🏆 Grupo {letra}",
            color=discord.Color.green()
        )

        conteudo = grupos[letra]

        if not conteudo:

            conteudo = [
                "📌 Nenhuma informação cadastrada."
            ]

        embed.description = "\n".join(
            conteudo
        )

        embed.set_footer(
            text="Sants Copa 2026"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):

    await bot.add_cog(
        Grupos(bot)
    )