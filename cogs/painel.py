import os
import discord

from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

from cogs.services.football_api import FootballAPI


CANAL_COPA_ID = int(os.getenv("CANAL_COPA_ID", 0))
MENSAGEM_COPA_ID = int(os.getenv("MENSAGEM_COPA_ID", 0))
CANAL_PALPITES_ID = int(os.getenv("CANAL_PALPITES_ID", 0))

BANNER_COPA_URL = os.getenv("BANNER_COPA_URL")


GROUPS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]


def now_br():
    return datetime.now().strftime("%d/%m/%Y às %H:%M")


def status_jogo(status):
    return {
        "SCHEDULED": "Agendado",
        "TIMED": "Agendado",
        "IN_PLAY": "Ao vivo",
        "PAUSED": "Intervalo",
        "FINISHED": "Finalizado",
        "POSTPONED": "Adiado",
        "CANCELLED": "Cancelado",
    }.get(status, status)


class GrupoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"Grupo {group}",
                value=group,
                emoji="🏆"
            )
            for group in GROUPS
        ]

        super().__init__(
            placeholder="Escolha um grupo para ver classificação e jogos...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="sants_copa_select_grupo"
        )

    async def callback(self, interaction: discord.Interaction):
        grupo = self.values[0]

        api = FootballAPI()
        standings = await api.get_standings()
        matches = await api.get_matches()

        embed = discord.Embed(
            title=f"🏆 Grupo {grupo} — Sants Copa 2026",
            description="Classificação, resultados e próximos jogos atualizados automaticamente.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Classificação",
            value=formatar_classificacao_grupo(standings, grupo),
            inline=False
        )

        embed.add_field(
            name="⚽ Jogos e Resultados",
            value=formatar_jogos_grupo(matches, grupo, api),
            inline=False
        )

        embed.set_footer(text=f"Atualizado em {now_br()}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class PainelCopaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GrupoSelect())

        if CANAL_PALPITES_ID:
            self.add_item(
                discord.ui.Button(
                    label="Ir para Palpites",
                    emoji="🎯",
                    style=discord.ButtonStyle.link,
                    url=f"https://discord.com/channels/{CANAL_COPA_ID}/{CANAL_PALPITES_ID}"
                )
            )

    @discord.ui.button(
        label="Regras",
        emoji="📜",
        style=discord.ButtonStyle.green,
        custom_id="sants_copa_regras"
    )
    async def regras(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal = f"<#{CANAL_PALPITES_ID}>" if CANAL_PALPITES_ID else "canal de palpites"

        await interaction.response.send_message(
            "📜 **Regras dos Palpites**\n\n"
            f"🎯 Envie seus palpites em {canal}.\n"
            "⏰ Palpites só valem antes da partida começar.\n"
            "✅ Vencedor correto: **+1 ponto**\n"
            "🎯 Placar exato: **+3 pontos**\n"
            "🔥 Zebra correta: **bônus especial**",
            ephemeral=True
        )


def formatar_classificacao_grupo(data, grupo):
    if not data or "standings" not in data:
        return "⚠️ Não consegui carregar a classificação agora."

    grupo_api = f"GROUP_{grupo}"

    for standing in data["standings"]:
        if standing.get("group") != grupo_api:
            continue

        linhas = []

        for team in standing.get("table", []):
            pos = team.get("position", "-")
            nome = team["team"].get("shortName") or team["team"].get("name")
            pts = team.get("points", 0)
            j = team.get("playedGames", 0)
            v = team.get("won", 0)
            e = team.get("draw", 0)
            d = team.get("lost", 0)
            sg = team.get("goalDifference", 0)

            linhas.append(
                f"`{pos}º` **{nome}** — **{pts} pts** | J:{j} V:{v} E:{e} D:{d} SG:{sg}"
            )

        return "\n".join(linhas) or "Grupo sem dados disponíveis."

    return "⚠️ Grupo ainda não encontrado pela API."


def formatar_jogos_grupo(data, grupo, api):
    if not data or "matches" not in data:
        return "⚠️ Não consegui carregar os jogos agora."

    grupo_api = f"GROUP_{grupo}"
    jogos = []

    for match in data["matches"]:
        if match.get("group") != grupo_api:
            continue

        casa = match["homeTeam"].get("shortName") or match["homeTeam"].get("name")
        fora = match["awayTeam"].get("shortName") or match["awayTeam"].get("name")
        status = status_jogo(match.get("status", "SCHEDULED"))
        horario = api.match_datetime_br(match.get("utcDate"))

        placar_casa = match["score"]["fullTime"]["home"]
        placar_fora = match["score"]["fullTime"]["away"]

        if placar_casa is None or placar_fora is None:
            jogos.append(f"⚽ **{casa} x {fora}**\n🕒 `{horario}` • `{status}`")
        else:
            jogos.append(f"✅ **{casa} {placar_casa} x {placar_fora} {fora}**\n📌 `{status}`")

    return "\n\n".join(jogos[:8]) or "Nenhum jogo encontrado para este grupo."


def buscar_grupo_brasil(standings):
    if not standings or "standings" not in standings:
        return "⚠️ Classificação indisponível no momento."

    for standing in standings["standings"]:
        tabela = standing.get("table", [])

        for team in tabela:
            nome = team["team"].get("name", "")

            if "Brazil" in nome or "Brasil" in nome:
                grupo = standing.get("group", "GROUP_C").replace("GROUP_", "")
                return f"**Grupo {grupo}**\n{formatar_classificacao_grupo(standings, grupo)}"

    return "🇧🇷 Grupo do Brasil ainda não localizado."


def buscar_jogos_destaque(matches, api):
    if not matches or "matches" not in matches:
        return "⚠️ Jogos indisponíveis no momento."

    jogos = []

    for match in matches["matches"]:
        status = match.get("status")

        if status not in ["IN_PLAY", "PAUSED", "SCHEDULED", "TIMED", "FINISHED"]:
            continue

        casa = match["homeTeam"].get("shortName") or match["homeTeam"].get("name")
        fora = match["awayTeam"].get("shortName") or match["awayTeam"].get("name")
        horario = api.match_datetime_br(match.get("utcDate"))
        status_formatado = status_jogo(status)

        placar_casa = match["score"]["fullTime"]["home"]
        placar_fora = match["score"]["fullTime"]["away"]

        if placar_casa is None or placar_fora is None:
            jogos.append(f"⚽ **{casa} x {fora}** — `{horario}`")
        else:
            jogos.append(f"✅ **{casa} {placar_casa} x {placar_fora} {fora}** — `{status_formatado}`")

        if len(jogos) >= 5:
            break

    return "\n".join(jogos) or "Nenhum jogo encontrado."


class PainelCopa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = FootballAPI()
        self.atualizar_painel.start()

    def cog_unload(self):
        self.atualizar_painel.cancel()

    async def criar_embed(self):
        matches = await self.api.get_matches()
        standings = await self.api.get_standings()

        embed = discord.Embed(
            title="🏆 SANTS COPA 2026",
            description=(
                "Central automática da Copa do Mundo.\n\n"
                "Use o menu abaixo para consultar grupos, jogos, resultados e pontuações."
            ),
            color=discord.Color.gold()
        )

        if BANNER_COPA_URL:
            embed.set_image(url=BANNER_COPA_URL)

        embed.add_field(
            name="⚽ Jogos em destaque",
            value=buscar_jogos_destaque(matches, self.api),
            inline=False
        )

        embed.add_field(
            name="🇧🇷 Grupo do Brasil",
            value=buscar_grupo_brasil(standings),
            inline=False
        )

        embed.add_field(
            name="🎯 Palpites",
            value=(
                f"Canal: <#{CANAL_PALPITES_ID}>\n"
                "Participe antes dos jogos começarem e dispute o ranking da Sants Copa."
                if CANAL_PALPITES_ID
                else "Configure `CANAL_PALPITES_ID` no Railway."
            ),
            inline=False
        )

        embed.add_field(
            name="📊 Consulta por grupos",
            value="Selecione qualquer grupo no menu abaixo para ver classificação, jogos e resultados.",
            inline=False
        )

        embed.set_footer(text=f"Última atualização • {now_br()} • Sants Copa")

        return embed

    @app_commands.command(
        name="painel_copa",
        description="Cria o painel automático da Sants Copa."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_copa(self, interaction: discord.Interaction):
        canal = interaction.channel

        msg = await canal.send(
            embed=await self.criar_embed(),
            view=PainelCopaView()
        )

        await interaction.response.send_message(
            f"✅ Painel criado com sucesso!\n\n"
            f"Coloque no Railway:\n"
            f"`MENSAGEM_COPA_ID={msg.id}`\n\n"
            f"Depois faça **Redeploy**.",
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

            await mensagem.edit(
                embed=await self.criar_embed(),
                view=PainelCopaView()
            )

            print("✅ Painel da Copa atualizado automaticamente.")

        except Exception as e:
            print(f"❌ Erro ao atualizar painel: {e}")


async def setup(bot):
    await bot.add_cog(PainelCopa(bot))