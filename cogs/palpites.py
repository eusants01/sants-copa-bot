import os
import discord

from discord.ext import commands
from discord import app_commands


CANAL_PALPITES_ID = int(os.getenv("CANAL_PALPITES_ID", 0))

BANNER_PALPITES_URL = os.getenv(
    "BANNER_PALPITES_URL",
    "https://cdn.discordapp.com/attachments/961677475191078992/1517408240634302645/content.png?ex=6a362c0c&is=6a34da8c&hm=0298a369156487db013d4edaf2bb8e681971a76aae6aeca3c50fb36d2903d1ac&"
)


JOGO_ATUAL = {
    "id": "brasil_haiti_2026",
    "titulo": "Brasil x Haiti",
    "horario": "21:30",
    "competicao": "Copa do Mundo",
}


class PalpiteModal(discord.ui.Modal, title="Enviar Palpite"):
    palpite = discord.ui.TextInput(
        label="Seu palpite",
        placeholder="Exemplo: Brasil 4x0 Haiti",
        max_length=40,
        required=True
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.registrar_palpite(
            interaction,
            str(self.palpite)
        )


class PalpitesView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Brasil 2x0 Haiti",
        emoji="🇧🇷",
        style=discord.ButtonStyle.success,
        custom_id="palpite_brasil_2x0_haiti"
    )
    async def brasil_2x0(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.registrar_palpite(interaction, "Brasil 2x0 Haiti")

    @discord.ui.button(
        label="Brasil 3x0 Haiti",
        emoji="🔥",
        style=discord.ButtonStyle.success,
        custom_id="palpite_brasil_3x0_haiti"
    )
    async def brasil_3x0(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.registrar_palpite(interaction, "Brasil 3x0 Haiti")

    @discord.ui.button(
        label="Brasil 3x1 Haiti",
        emoji="⚽",
        style=discord.ButtonStyle.primary,
        custom_id="palpite_brasil_3x1_haiti"
    )
    async def brasil_3x1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.registrar_palpite(interaction, "Brasil 3x1 Haiti")

    @discord.ui.button(
        label="Outro Palpite",
        emoji="✍️",
        style=discord.ButtonStyle.secondary,
        custom_id="palpite_outro"
    )
    async def outro_palpite(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PalpiteModal(self.cog))

    @discord.ui.button(
        label="Ver Palpites",
        emoji="📊",
        style=discord.ButtonStyle.secondary,
        custom_id="ver_palpites"
    )
    async def ver_palpites(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.mostrar_palpites(interaction)


class Palpites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def criar_tabela(self):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS palpites (
                    id SERIAL PRIMARY KEY,
                    jogo_id TEXT NOT NULL,
                    jogo_titulo TEXT NOT NULL,
                    user_id BIGINT NOT NULL,
                    user_name TEXT NOT NULL,
                    palpite TEXT NOT NULL,
                    criado_em TIMESTAMP DEFAULT NOW(),
                    UNIQUE(jogo_id, user_id)
                );
            """)

    async def cog_load(self):
        await self.criar_tabela()
        self.bot.add_view(PalpitesView(self))

    async def registrar_palpite(self, interaction: discord.Interaction, palpite: str):
        async with self.bot.pool.acquire() as conn:
            existe = await conn.fetchrow(
                """
                SELECT palpite FROM palpites
                WHERE jogo_id = $1 AND user_id = $2
                """,
                JOGO_ATUAL["id"],
                interaction.user.id
            )

            if existe:
                return await interaction.response.send_message(
                    f"⚠️ Você já enviou um palpite para este jogo.\n\n"
                    f"📊 Seu palpite atual: **{existe['palpite']}**",
                    ephemeral=True
                )

            await conn.execute(
                """
                INSERT INTO palpites (
                    jogo_id,
                    jogo_titulo,
                    user_id,
                    user_name,
                    palpite
                )
                VALUES ($1, $2, $3, $4, $5)
                """,
                JOGO_ATUAL["id"],
                JOGO_ATUAL["titulo"],
                interaction.user.id,
                interaction.user.display_name,
                palpite
            )

        await interaction.response.send_message(
            f"✅ Palpite registrado com sucesso!\n\n"
            f"📊 Seu palpite: **{palpite}**",
            ephemeral=True
        )

    async def mostrar_palpites(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            palpites = await conn.fetch(
                """
                SELECT user_name, palpite
                FROM palpites
                WHERE jogo_id = $1
                ORDER BY criado_em ASC
                LIMIT 25
                """,
                JOGO_ATUAL["id"]
            )

        if not palpites:
            return await interaction.response.send_message(
                "📭 Ainda não há palpites registrados para este jogo.",
                ephemeral=True
            )

        descricao = ""

        for index, row in enumerate(palpites, start=1):
            descricao += (
                f"`{index}.` **{row['user_name']}**\n"
                f"└ 📊 {row['palpite']}\n\n"
            )

        embed = discord.Embed(
            title="📊 Palpites da Galera",
            description=descricao,
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text=f"{JOGO_ATUAL['titulo']} • {len(palpites)} palpites exibidos"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=False
        )

    @app_commands.command(
        name="palpites",
        description="Envia o painel oficial de palpites do jogo do dia."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def palpites(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🇧🇷 Brasil x Haiti 🇭🇹",
            description=(
                "A Seleção Brasileira entra em campo hoje e a comunidade "
                "já pode registrar seus palpites.\n\n"
                "📊 **Qual será o placar da partida?**\n"
                "Escolha uma opção abaixo ou envie seu próprio resultado."
            ),
            color=discord.Color.green()
        )

        embed.add_field(
            name="⏰ Horário",
            value=f"**{JOGO_ATUAL['horario']}**",
            inline=True
        )

        embed.add_field(
            name="🏆 Competição",
            value=f"**{JOGO_ATUAL['competicao']}**",
            inline=True
        )

        embed.add_field(
            name="🎯 Participação",
            value="Clique em um botão abaixo para registrar seu palpite.",
            inline=False
        )

        if BANNER_PALPITES_URL:
            embed.set_image(url=BANNER_PALPITES_URL)

        embed.set_footer(
            text="Nebularis • Um universo de grandes momentos."
        )

        canal = interaction.guild.get_channel(CANAL_PALPITES_ID)

        if canal is None:
            canal = interaction.channel

        await canal.send(
            embed=embed,
            view=PalpitesView(self)
        )

        await interaction.response.send_message(
            "✅ Painel de palpites enviado com sucesso.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Palpites(bot))