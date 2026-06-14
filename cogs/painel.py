import os
import aiohttp
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime


CANAL_COPA_ID = int(os.getenv("CANAL_COPA_ID", 0))
MENSAGEM_COPA_ID = int(os.getenv("MENSAGEM_COPA_ID", 0))
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

BANNER_URL = "https://i.imgur.com/SEU_BANNER_AQUI.png"

BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "WC"


class PainelCopa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.atualizar_painel.start()

    def cog_unload(self):
        self.atualizar_painel.cancel()

    async def api_get(self, endpoint):
        headers = {"X-Auth-Token": FOOTBALL_API_KEY}

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}{endpoint}", headers=headers) as resp:
                if resp.status != 200:
                    print(f"Erro API {resp.status}: {await resp.text()}")
                    return None

                return await resp.json()

    async def buscar_jogos(self):
        return await self.api_get(f"/competitions/{COMPETITION}/matches")

    async def buscar_classificacao(self):
        return await self.api_get(f"/competitions/{COMPETITION}/standings")

    def formatar_jogos(self, data):
        if not data or "matches" not in data:
            return "⚠️ Não consegui carregar os jogos agora."

        jogos = data["matches"][:6]

        texto = ""

        for jogo in jogos:
            casa = jogo["homeTeam"]["shortName"]
            fora = jogo["awayTeam"]["shortName"]
            status = jogo["status"]

            placar_casa = jogo["score"]["fullTime"]["home"]
            placar_fora = jogo["score"]["fullTime"]["away"]

            if placar_casa is None:
                texto += f"⚽ **{casa} x {fora}** — `{status}`\n"
            else:
                texto += f"✅ **{casa} {placar_casa} x {placar_fora} {fora}** — `{status}`\n"

        return texto or "Nenhum jogo encontrado."

    def formatar_grupo_brasil(self, data):
        if not data or "standings" not in data:
            return "⚠️ Não consegui carregar a classificação."

        for standing in data["standings"]:
            group = standing.get("group", "")

            for time in standing["table"]:
                nome = time["team"]["name"]

                if "Brazil" in nome or "Brasil" in nome:
                    linhas = []

                    for posicao in standing["table"]:
                        equipe = posicao["team"]["shortName"]
                        pontos = posicao["points"]
                        jogos = posicao["playedGames"]
                        saldo = posicao["goalDifference"]

                        linhas.append(
                            f"`{posicao['position']}º` **{equipe}** — {pontos} pts | J:{jogos} | SG:{saldo}"
                        )

                    return "\n".join(linhas)

        return "🇧🇷 Grupo do Brasil ainda não encontrado."

    async def criar_embed(self):
        jogos = await self.buscar_jogos()
        classificacao = await self.buscar_classificacao()

        agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

        embed = discord.Embed(
            title="🏆 SANTS COPA 2026",
            description=(
                "☠️ **Painel oficial da Copa na Família Sant's**\n\n"
                "Atualização automática com jogos, resultados e classificação."
            ),
            color=discord.Color.gold()
        )

        embed.set_image(url=BANNER_URL)

        embed.add_field(
            name="⚽ Jogos / Resultados",
            value=self.formatar_jogos(jogos),
            inline=False
        )

        embed.add_field(
            name="🇧🇷 Grupo do Brasil",
            value=self.formatar_grupo_brasil(classificacao),
            inline=False
        )

        embed.add_field(
            name="🎯 Sistema Sants Copa",
            value=(
                "• Palpites antes dos jogos\n"
                "• Ranking automático\n"
                "• Medalhas especiais\n"
                "• Jornada One Piece rumo ao Hexa"
            ),
            inline=False
        )

        embed.set_footer(text=f"Atualizado automaticamente • {agora}")

        return embed

    @app_commands.command(name="painel_copa", description="Cria o painel automático da Sants Copa.")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_copa(self, interaction: discord.Interaction):
        embed = await self.criar_embed()

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await interaction.followup.send(
            f"✅ Painel criado!\nColoque no Railway:\n`MENSAGEM_COPA_ID={msg.id}`",
            ephemeral=True
        )

    @tasks.loop(minutes=10)
    async def atualizar_painel(self):
        await self.bot.wait_until_ready()

        if CANAL_COPA_ID == 0 or MENSAGEM_COPA_ID == 0:
            return

        canal = self.bot.get_channel(CANAL_COPA_ID)

        if not canal:
            return

        try:
            mensagem = await canal.fetch_message(MENSAGEM_COPA_ID)
            embed = await self.criar_embed()
            await mensagem.edit(embed=embed)
            print("✅ Painel atualizado automaticamente.")
        except Exception as e:
            print(f"❌ Erro ao atualizar painel: {e}")


async def setup(bot):
    await bot.add_cog(PainelCopa(bot))