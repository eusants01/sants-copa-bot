import os
import aiohttp
import discord

from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime


CANAL_COPA_ID = int(os.getenv("CANAL_COPA_ID", 0))
CANAL_PALPITES_ID = int(os.getenv("CANAL_PALPITES_ID", 0))
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

        if CANAL_PALPITES_ID:
            self.add_item(
                discord.ui.Button(
                    label="Ir para Palpites",
                    emoji="🎯",
                    style=discord.ButtonStyle.link,
                    url=f"https://discord.com/channels/@me/{CANAL_PALPITES_ID}"
                )
            )

    @discord.ui.button(
        label="Regras dos Palpites",
        emoji="📜",
        style=discord.ButtonStyle.green,
        custom_id="sants_copa_regras"
    )
    async def regras(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal = f"<#{CANAL_PALPITES_ID}>" if CANAL_PALPITES_ID else "canal de palpites"

        await interaction.response.send_message(
            "📜 **Regras dos Palpites**\n\n"
            f"🎯 Os palpites devem ser enviados em {canal}.\n"
            "⏰ Palpites só valem antes do início da partida.\n"
            "✅ Acertou o vencedor: **+1 ponto**\n"
            "🎯 Acertou o placar exato: **+3 pontos**\n"
            "🔥 Acertou uma zebra: **bônus especial**\n\n"
            "🏆 Os melhores colocados entram no ranking oficial da Sants Copa.",
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
            "🏆 **Ranking da Sants Copa**\n\n"
            "O ranking automático será liberado na próxima etapa do bot.\n"
            "Por enquanto, o painel ficará responsável pelos jogos, resultados e classificação.",
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

        headers = {"X-Auth-Token": FOOTBALL_API_KEY}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
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

    def status_jogo(self, status: str):
        status_map = {
            "SCHEDULED": "Agendado",
            "TIMED": "Agendado",
            "IN_PLAY": "Ao vivo",
            "PAUSED": "Intervalo",
            "FINISHED": "Finalizado",
            "POSTPONED": "Adiado",
            "CANCELLED": "Cancelado"
        }

        return status_map.get(status, status)

    def formatar_jogos(self, data):
        if not data or "matches" not in data:
            return (
                "⚠️ Não consegui carregar os jogos agora.\n"
                "O painel tentará atualizar novamente em alguns minutos."
            )

        jogos = data["matches"][:8]
        linhas = []

        for jogo in jogos:
            casa = jogo["homeTeam"].get("shortName") or jogo["homeTeam"].get("name")
            fora = jogo["awayTeam"].get("shortName") or jogo["awayTeam"].get("name")
            status = self.status_jogo(jogo.get("status", "SCHEDULED"))
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

    async def criar_embed(self):
        jogos = await self.buscar_jogos()
        classificacao = await self.buscar_classificacao()

        agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
        canal_palpites = f"<#{CANAL_PALPITES_ID}>" if CANAL_PALPITES_ID else "canal de palpites"

        embed = discord.Embed(
            title="🏆 SANTS COPA 2026",
            description=(
                "Central oficial da Copa do Mundo no servidor.\n\n"
                "Acompanhe jogos, resultados, classificação e participe dos palpites."
            ),
            color=discord.Color.green()
        )

        embed.set_image(url=BANNER_COPA_URL)

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
            name="🎯 Palpites",
            value=(
                f"Envie seus palpites em {canal_palpites} antes dos jogos começarem.\n\n"
                "✅ Vencedor correto: **+1 ponto**\n"
                "🎯 Placar exato: **+3 pontos**\n"
                "🔥 Zebra correta: **bônus especial**"
            ),
            inline=False
        )

        embed.add_field(
            name="📌 Atualização automática",
            value=(
                "Este painel atualiza sozinho com os dados mais recentes da Copa.\n"
                "Resultados e classificações podem depender da disponibilidade da API."
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Última atualização • {agora} • Sants Copa"
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
            f"No Railway, coloque:\n"
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