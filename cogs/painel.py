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


def lista_texto(lista, vazio="Nenhuma informação cadastrada."):
    return "\n".join(lista) if lista else vazio


class GrupoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"Grupo {letra}",
                value=letra,
                emoji="🏆"
            )
            for letra in "ABCDEFGHIJKL"
        ]

        super().__init__(
            placeholder="📊 Escolha um grupo para consultar...",
            options=options,
            custom_id="sants_copa_grupo_select"
        )

    async def callback(self, interaction: discord.Interaction):
        grupo = self.values[0]
        dados = CopaService.carregar()
        grupos = dados.get("grupos", {})
        conteudo = grupos.get(grupo, [])

        embed = discord.Embed(
            title=f"🏆 Grupo {grupo}",
            description=lista_texto(conteudo, "📌 Grupo ainda sem informações cadastradas."),
            color=discord.Color.green()
        )

        embed.set_footer(text=f"Sants Copa 2026 • {agora()}")

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


class PainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GrupoSelect())

    @discord.ui.button(
        label="Jogos",
        emoji="📅",
        style=discord.ButtonStyle.green,
        custom_id="sants_copa_jogos"
    )
    async def jogos(self, interaction: discord.Interaction, button: discord.ui.Button):
        dados = CopaService.carregar()

        embed = discord.Embed(
            title="📅 Jogos da Sants Copa",
            color=discord.Color.green()
        )

        embed.add_field(
            name="⚽ Jogos de Hoje",
            value=lista_texto(dados.get("jogos_hoje", []), "📌 Nenhum jogo cadastrado para hoje."),
            inline=False
        )

        embed.add_field(
            name="⏳ Próximos Jogos",
            value=lista_texto(dados.get("proximos_jogos", []), "📌 Nenhum próximo jogo cadastrado."),
            inline=False
        )

        embed.set_footer(text=f"Sants Copa 2026 • {agora()}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Palpites",
        emoji="🎯",
        style=discord.ButtonStyle.blurple,
        custom_id="sants_copa_palpites"
    )
    async def palpites(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal = f"<#{CANAL_PALPITES_ID}>" if CANAL_PALPITES_ID else "canal não configurado"

        await interaction.response.send_message(
            f"🎯 **Palpites da Sants Copa**\n\n"
            f"Envie seus palpites em {canal} antes dos jogos começarem.\n\n"
            f"✅ Vencedor correto: **+1 ponto**\n"
            f"🎯 Placar exato: **+3 pontos**\n"
            f"🔥 Zebra correta: **bônus especial**",
            ephemeral=True
        )

    @discord.ui.button(
        label="Regras",
        emoji="📜",
        style=discord.ButtonStyle.gray,
        custom_id="sants_copa_regras"
    )
    async def regras(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📜 **Regras Oficiais — Sants Copa 2026**\n\n"
            "1. Os palpites devem ser enviados antes do início da partida.\n"
            "2. Palpites editados após o início do jogo serão desconsiderados.\n"
            "3. Acertar o vencedor concede **+1 ponto**.\n"
            "4. Acertar o placar exato concede **+3 pontos**.\n"
            "5. O ranking será atualizado conforme a administração validar os resultados.\n\n"
            "🏆 No fim da Copa, os melhores palpiteiros receberão destaque no servidor.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Ranking",
        emoji="🏅",
        style=discord.ButtonStyle.green,
        custom_id="sants_copa_ranking"
    )
    async def ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        dados = CopaService.carregar()

        embed = discord.Embed(
            title="🏅 Ranking dos Palpiteiros",
            description=lista_texto(dados.get("ranking", []), "Ranking ainda vazio."),
            color=discord.Color.gold()
        )

        embed.set_footer(text=f"Sants Copa 2026 • {agora()}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class PainelCopa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.atualizar_painel.start()

    def cog_unload(self):
        self.atualizar_painel.cancel()

    def criar_embed(self):
        dados = CopaService.carregar()
        brasil = dados.get("selecao_brasil", {})

        embed = discord.Embed(
            title="🏆 SANTS COPA 2026",
            description=(
                "━━━━━━━━━━━━━━\n"
                "🇧🇷 **Brasil rumo ao Hexa**\n"
                "━━━━━━━━━━━━━━"
            ),
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🔥 Destaque da Rodada",
            value=lista_texto(dados.get("destaque", []), "Nenhum destaque cadastrado."),
            inline=False
        )

        embed.add_field(
    name="🇧🇷 Seleção Brasileira",
    value=(
        f"🏆 Grupo: **{brasil.get('grupo', '-')}**\n"
        f"🏅 Posição: **{brasil.get('posicao', '-')}**\n"
        f"⭐ Pontos: **{brasil.get('pontos', 0)}**\n"
        f"⚽ Jogos: **{brasil.get('jogos', 0)}**\n"
        f"✅ Vitórias: **{brasil.get('vitorias', 0)}**\n"
        f"🤝 Empates: **{brasil.get('empates', 0)}**\n"
        f"❌ Derrotas: **{brasil.get('derrotas', 0)}**\n"
        f"🥅 Saldo de gols: **{brasil.get('saldo_gols', 0)}**\n\n"
        f"⏳ Próximo jogo: **{brasil.get('proximo_jogo', 'A definir')}**\n"
        f"📅 Data: **{brasil.get('data', 'A definir')}**\n"
        f"🕒 Horário: **{brasil.get('horario', 'A definir')}**\n"
        f"🟡 Status: **{brasil.get('status', 'A definir')}**"
    ),
    inline=False
)

        embed.add_field(
            name="⚽ Jogos de Hoje",
            value=lista_texto(dados.get("jogos_hoje", []), "📌 Nenhum jogo cadastrado para hoje."),
            inline=False
        )

        embed.add_field(
            name="⏳ Próximos Jogos",
            value=lista_texto(dados.get("proximos_jogos", []), "📌 Nenhum próximo jogo cadastrado."),
            inline=False
        )

        embed.add_field(
            name="🎯 Palpites",
            value=(
                f"Canal: <#{CANAL_PALPITES_ID}>\n"
                "Participe antes dos jogos começarem e dispute o ranking."
                if CANAL_PALPITES_ID
                else "Canal de palpites não configurado."
            ),
            inline=False
        )

        embed.add_field(
            name="🏅 Ranking",
            value=lista_texto(dados.get("ranking", []), "Ranking ainda vazio."),
            inline=False
        )

        if BANNER_COPA_URL:
            embed.set_image(url=BANNER_COPA_URL)

        embed.set_footer(text=f"Última atualização • {agora()} • Sants Copa")

        return embed

    @app_commands.command(
        name="painel_copa",
        description="Cria o painel oficial da Sants Copa."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_copa(self, interaction: discord.Interaction):
        painel = await interaction.channel.send(
            embed=self.criar_embed(),
            view=PainelView()
        )

        await interaction.response.send_message(
            f"✅ Painel criado com sucesso!\n\n"
            f"🆔 MENSAGEM_COPA_ID:\n`{painel.id}`",
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
            await mensagem.edit(
                embed=self.criar_embed(),
                view=PainelView()
            )
            print("✅ Painel da Sants Copa atualizado.")
        except Exception as erro:
            print(f"❌ Erro ao atualizar painel: {erro}")


async def setup(bot):
    await bot.add_cog(PainelCopa(bot))