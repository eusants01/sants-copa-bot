import os
import aiohttp
import discord

from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime


CANAL_COPA_ID = int(os.getenv("CANAL_COPA_ID", 0))
MENSAGEM_COPA_ID = int(os.getenv("MENSAGEM_COPA_ID", 0))
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

BANNER_COPA_URL = os.getenv(
    "BANNER_COPA_URL",
    "https://i.imgur.com/SEU_BANNER_AQUI.png"
)

BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "WC"


class PainelCopaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Palpites",
        emoji="🎯",
        style=discord.ButtonStyle.green,
        custom_id="sants_copa_palpites"
    )
    async def palpites(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🎯 **Sistema de Palpites**\n\n"
            "Faça seus palpites antes dos jogos começarem e dispute o topo do ranking da Família Sant's.\n\n"
            "Em breve: `/palpite`",
            ephemeral=True
        )

    @discord.ui.button(
        label="Ranking",
        emoji="🏆",
        style=discord.ButtonStyle.blurple,
        custom_id="sants_copa_ranking"
    )
    async def ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🏆 **Ranking Sants Copa**\n\n"
            "Os melhores palpiteiros aparecerão aqui com pontuação, acertos e medalhas especiais.\n\n"
            "Em breve: `/ranking_copa`",
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
            "📜 **Regras da Sants Copa**\n\n"
            "✅ Acertou vencedor: **+1 ponto**\n"
            "✅ Acertou placar exato: **+3 pontos**\n"
            "🔥 Acertou zebra: **pontos extras**\n"
            "⏰ Palpites encerram quando o jogo começa.\n\n"
            "☠️ No fim da Copa, os melhores recebem cargos e premiações.",
            ephemeral=True
        )


class PainelCopa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.atualizar_painel.start()

    def cog_unload(self):
        self.atualizar_painel.cancel()

    async def api_get(self, endpoint: str):
        if not FOOTBALL_API_KEY:
            return None

        headers = {
            "X-Auth-Token": FOOTBALL_API_KEY
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BASE_URL}{endpoint}",
                    headers=headers
                ) as response:

                    if response.status != 200:
                        print(f"❌ Erro API {response.status}: {await response.text()}")
                        return None

                    return await response.json()

        except Exception as e:
            print(f"❌ Erro ao consultar API: {e}")
            return None

    async def buscar_jogos(self):
        return await self.api_get(f"/competitions/{COMPETITION}/matches")

    async def buscar_classificacao(self):
        return await self.api_get(f"/competitions/{COMPETITION}/standings")

    def formatar_data(self, utc_date: str):
        if not utc_date:
            return "Horário indefinido"

        try:
            data = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
            return data.strftime("%d/%m às %H:%M")
        except Exception:
            return "Horário indefinido"

    def formatar_jogos(self, data):
        if not data or "matches" not in data:
            return (
                "⚠️ Não consegui carregar os jogos agora.\n"
                "O painel tentará atualizar novamente automaticamente."
            )

        jogos = data["matches"][:6]

        linhas = []

        for jogo in jogos:
            casa = jogo["homeTeam"].get("shortName") or jogo["homeTeam"].get("name")
            fora = jogo["awayTeam"].get("shortName") or jogo["awayTeam"].get("name")
            status = jogo.get("status", "SCHEDULED")
            horario = self.formatar_data(jogo.get("utcDate"))

            placar_casa = jogo["score"]["fullTime"]["home"]
            placar_fora = jogo["score"]["fullTime"]["away"]

            if placar_casa is None or placar_fora is None:
                linhas.append(
                    f"⚽ **{casa} x {fora}**\n"
                    f"🕒 `{horario}` • `{status}`"
                )
            else:
                linhas.append(
                    f"✅ **{casa} {placar_casa} x {placar_fora} {fora}**\n"
                    f"📌 `{status}`"
                )

        return "\n\n".join(linhas) or "Nenhum jogo encontrado."

    def formatar_grupo_brasil(self, data):
        if not data or "standings" not in data:
            return (
                "⚠️ Classificação indisponível no momento.\n"
                "A próxima atualização tentará carregar novamente."
            )

        for standing in data["standings"]:
            tabela = standing.get("table", [])

            encontrou_brasil = any(
                "Brazil" in time["team"].get("name", "")
                or "Brasil" in time["team"].get("name", "")
                for time in tabela
            )

            if encontrou_brasil:
                linhas = []

                for time in tabela:
                    pos = time.get("position", "-")
                    nome = time["team"].get("shortName") or time["team"].get("name")
                    pontos = time.get("points", 0)
                    jogos = time.get("playedGames", 0)
                    vitorias = time.get("won", 0)
                    empates = time.get("draw", 0)
                    derrotas = time.get("lost", 0)
                    saldo = time.get("goalDifference", 0)

                    linhas.append(
                        f"`{pos}º` **{nome}** — **{pontos} pts** "
                        f"| J:{jogos} V:{vitorias} E:{empates} D:{derrotas} SG:{saldo}"
                    )

                return "\n".join(linhas)

        return "🇧🇷 Grupo do Brasil ainda não localizado pela API."

    def mensagem_status(self):
        return (
            "💚💛 **Rumo ao Hexa!**\n"
            "Acompanhe jogos, resultados, palpites e ranking da Copa diretamente pela Família Sant's."
        )

    async def criar_embed(self):
        jogos = await self.buscar_jogos()
        classificacao = await self.buscar_classificacao()

        agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

        embed = discord.Embed(
            title="🏆 SANTS COPA 2026",
            description=(
                "☠️ **Central oficial da Copa do Mundo na Família Sant's**\n\n"
                "Um painel automático para acompanhar a Copa, fazer palpites, "
                "ver resultados e disputar o título de melhor palpiteiro do servidor."
            ),
            color=discord.Color.gold()
        )

        embed.set_image(url=BANNER_COPA_URL)

        embed.add_field(
            name="🌎 Status da Copa",
            value=self.mensagem_status(),
            inline=False
        )

        embed.add_field(
            name="⚽ Jogos e Resultados",
            value=self.formatar_jogos(jogos),
            inline=False
        )

        embed.add_field(
            name="🇧🇷 Grupo do Brasil",
            value=self.formatar_grupo_brasil(classificacao),
            inline=False
        )

        embed.add_field(
            name="🎯 Pontuação dos Palpites",
            value=(
                "✅ Vencedor correto: **+1 ponto**\n"
                "🎯 Placar exato: **+3 pontos**\n"
                "🔥 Zebra correta: **bônus especial**\n"
                "🏆 Ranking atualizado automaticamente"
            ),
            inline=True
        )

        embed.add_field(
            name="☠️ Jornada One Piece",
            value=(
                "🌊 East Blue — Fase de grupos\n"
                "🧭 Grand Line — Mata-mata\n"
                "🔥 Wano — Semifinal\n"
                "🏴‍☠️ Laugh Tale — Final"
            ),
            inline=True
        )

        embed.add_field(
            name="📌 Como participar",
            value=(
                "Use os botões abaixo para ver regras, palpites e ranking.\n"
                "Os comandos oficiais serão liberados conforme o sistema evoluir."
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Atualizado automaticamente • {agora} • Sants Copa"
        )

        return embed

    @app_commands.command(
        name="painel_copa",
        description="Cria o painel oficial automático da Sants Copa."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_copa(self, interaction: discord.Interaction):
        embed = await self.criar_embed()
        view = PainelCopaView()

        canal = interaction.channel
        msg = await canal.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"✅ **Painel criado com sucesso!**\n\n"
            f"📌 Canal: {canal.mention}\n"
            f"🆔 ID da mensagem: `{msg.id}`\n\n"
            f"Agora vá no Railway e coloque:\n"
            f"`MENSAGEM_COPA_ID={msg.id}`\n\n"
            f"Depois clique em **Redeploy**.",
            ephemeral=True
        )

    @tasks.loop(minutes=10)
    async def atualizar_painel(self):
        await self.bot.wait_until_ready()

        if CANAL_COPA_ID == 0 or MENSAGEM_COPA_ID == 0:
            return

        canal = self.bot.get_channel(CANAL_COPA_ID)

        if not canal:
            print("❌ Canal da Copa não encontrado.")
            return

        try:
            mensagem = await canal.fetch_message(MENSAGEM_COPA_ID)
            embed = await self.criar_embed()

            await mensagem.edit(
                embed=embed,
                view=PainelCopaView()
            )

            print("✅ Painel da Sants Copa atualizado.")

        except Exception as e:
            print(f"❌ Erro ao atualizar painel: {e}")


async def setup(bot):
    await bot.add_cog(PainelCopa(bot))