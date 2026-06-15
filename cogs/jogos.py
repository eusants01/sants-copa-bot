import discord

from discord.ext import commands
from discord import app_commands

from cogs.services.copa_service import CopaService


class Jogos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="adicionar_jogo_hoje",
        description="Adiciona um jogo na área Jogos de Hoje."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def adicionar_jogo_hoje(
        self,
        interaction: discord.Interaction,
        jogo: str
    ):
        dados = CopaService.carregar()

        dados.setdefault("jogos_hoje", [])
        dados["jogos_hoje"].append(jogo)

        CopaService.salvar(dados)

        await interaction.response.send_message(
            f"✅ Jogo adicionado em **Jogos de Hoje**:\n`{jogo}`",
            ephemeral=True
        )

    @app_commands.command(
        name="adicionar_proximo_jogo",
        description="Adiciona um jogo na área Próximos Jogos."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def adicionar_proximo_jogo(
        self,
        interaction: discord.Interaction,
        jogo: str
    ):
        dados = CopaService.carregar()

        dados.setdefault("proximos_jogos", [])
        dados["proximos_jogos"].append(jogo)

        CopaService.salvar(dados)

        await interaction.response.send_message(
            f"✅ Jogo adicionado em **Próximos Jogos**:\n`{jogo}`",
            ephemeral=True
        )

    @app_commands.command(
        name="limpar_jogos_hoje",
        description="Limpa todos os jogos de hoje."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def limpar_jogos_hoje(
        self,
        interaction: discord.Interaction
    ):
        dados = CopaService.carregar()

        dados["jogos_hoje"] = []

        CopaService.salvar(dados)

        await interaction.response.send_message(
            "✅ Jogos de hoje limpos com sucesso.",
            ephemeral=True
        )

    @app_commands.command(
        name="limpar_proximos_jogos",
        description="Limpa todos os próximos jogos."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def limpar_proximos_jogos(
        self,
        interaction: discord.Interaction
    ):
        dados = CopaService.carregar()

        dados["proximos_jogos"] = []

        CopaService.salvar(dados)

        await interaction.response.send_message(
            "✅ Próximos jogos limpos com sucesso.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Jogos(bot))