import os
import discord

from discord.ext import commands, tasks
from discord import app_commands

from datetime import datetime

from cogs.services.copa_service import CopaService


CANAL_COPA_ID = int(
    os.getenv(
        "CANAL_COPA_ID",
        0
    )
)

MENSAGEM_COPA_ID = int(
    os.getenv(
        "MENSAGEM_COPA_ID",
        0
    )
)

CANAL_PALPITES_ID = int(
    os.getenv(
        "CANAL_PALPITES_ID",
        0
    )
)

BANNER_COPA_URL = os.getenv(
    "BANNER_COPA_URL"
)


class GrupoSelect(
    discord.ui.Select
):

    def __init__(self):

        options = []

        for letra in "ABCDEFGHIJKL":

            options.append(

                discord.SelectOption(

                    label=f"Grupo {letra}",

                    value=letra,

                    emoji="🏆"

                )

            )

        super().__init__(

            placeholder="Escolha um grupo...",

            options=options,

            custom_id="grupo_select"

        )

    async def callback(

        self,

        interaction: discord.Interaction

    ):

        grupo = self.values[0]

        dados = CopaService.carregar()

        conteudo = dados["grupos"].get(

            grupo,

            []

        )

        embed = discord.Embed(

            title=f"🏆 Grupo {grupo}",

            color=discord.Color.green()

        )

        if conteudo:

            embed.description = "\n".join(

                conteudo

            )

        else:

            embed.description = (

                "📌 Nenhum dado disponível."

            )

        await interaction.response.send_message(

            embed=embed,

            ephemeral=True

        )


class PainelView(

    discord.ui.View

):

    def __init__(self):

        super().__init__(

            timeout=None

        )

        self.add_item(

            GrupoSelect()

        )

    @discord.ui.button(

        label="Brasil",

        emoji="🇧🇷",

        style=discord.ButtonStyle.green,

        custom_id="brasil"

    )

    async def brasil(

        self,

        interaction:

        discord.Interaction,

        button:

        discord.ui.Button

    ):

        await interaction.response.send_message(

            "🇧🇷 Brasil está no Grupo C.",

            ephemeral=True

        )

    @discord.ui.button(

        label="Palpites",

        emoji="🎯",

        style=discord.ButtonStyle.blurple,

        custom_id="palpites"

    )

    async def palpites(

        self,

        interaction:

        discord.Interaction,

        button:

        discord.ui.Button

    ):

        if CANAL_PALPITES_ID:

            await interaction.response.send_message(

                f"🎯 Canal: <#{CANAL_PALPITES_ID}>",

                ephemeral=True

            )

        else:

            await interaction.response.send_message(

                "❌ Canal não configurado.",

                ephemeral=True

            )

    @discord.ui.button(

        label="Regras",

        emoji="📜",

        style=discord.ButtonStyle.gray,

        custom_id="regras"

    )

    async def regras(

        self,

        interaction:

        discord.Interaction,

        button:

        discord.ui.Button

    ):

        await interaction.response.send_message(

            "📜 Acertou vencedor = +1\n🎯 Acertou placar = +3",

            ephemeral=True

        )


class PainelCopa(

    commands.Cog

):

    def __init__(

        self,

        bot

    ):

        self.bot = bot

        self.atualizar_painel.start()

    def criar_embed(

        self

    ):

        dados = CopaService.carregar()

        embed = discord.Embed(

            title="🏆 SANTS COPA 2026",

            description="Central oficial da Copa.",

            color=discord.Color.gold()

        )

        if BANNER_COPA_URL:

            embed.set_image(

                url=BANNER_COPA_URL

            )

        embed.add_field(

            name="🔥 Destaque",

            value=dados["destaque"],

            inline=False

        )

        embed.add_field(

            name="⚽ Jogos de Hoje",

            value="\n".join(

                dados["jogos_hoje"]

            ),

            inline=False

        )

        embed.add_field(

            name="⏳ Próximos Jogos",

            value="\n".join(

                dados["proximos_jogos"]

            ),

            inline=False

        )

        embed.add_field(

            name="🥇 Ranking",

            value="\n".join(

                dados["ranking"]

            ),

            inline=False

        )

        embed.set_footer(

            text=f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        )

        return embed

    @app_commands.command(

        name="painel_copa",

        description="Cria o painel da Copa."

    )

    async def painel_copa(

        self,

        interaction:

        discord.Interaction

    ):

        painel = await interaction.channel.send(

            embed=self.criar_embed(),

            view=PainelView()

        )

        await interaction.response.send_message(

            f"🆔 `{painel.id}`",

            ephemeral=True

        )

    @tasks.loop(

        minutes=10

    )

    async def atualizar_painel(

        self

    ):

        pass


async def setup(

    bot

):

    await bot.add_cog(

        PainelCopa(bot)

    )