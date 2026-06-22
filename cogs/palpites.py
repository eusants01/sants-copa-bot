import os
import discord
import traceback

from datetime import datetime
from discord.ext import commands
from discord import app_commands
from collections import Counter
from zoneinfo import ZoneInfo


# ─── Configuração ────────────────────────────────────────────────────────────

CANAL_PALPITES_ID = int(os.getenv("CANAL_PALPITES_ID", 0))

BANNER_PALPITES_URL = os.getenv(
    "BANNER_PALPITES_URL",
    "https://cdn.discordapp.com/attachments/961677475191078992/1518502687946051765/content.png?ex=6a3a2755&is=6a38d5d5&hm=cf77267c1842023896721ddc1989bf45b3a92fe47a42ee46420eec6027555e90&"
)

FUSO = ZoneInfo("America/Sao_Paulo")

JOGO_ATUAL = {
    "id":         "brasil_escocia_2026",
    "titulo":     "Brasil x Escócia",
    "horario":    "19:00",
    "data":       "24/06",
    "competicao": "Copa do Mundo 2026",
    "inicio":     datetime(2026, 6, 24, 19, 0, tzinfo=FUSO),
}

COR_PRINCIPAL = 0x7B4FDB
COR_OURO      = 0xFFD700
COR_PRATA     = 0xC0C0C0
COR_ERRO      = 0xFF4C4C
COR_SUCESSO   = 0x43B581


# ─── Helpers ─────────────────────────────────────────────────────────────────

def jogo_ja_comecou() -> bool:
    return datetime.now(tz=FUSO) >= JOGO_ATUAL["inicio"]


def _embed_base(title: str, description: str = "", color: int = COR_PRINCIPAL) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Nebularis • Um universo de grandes momentos.")
    return embed


async def _responder_erro(interaction: discord.Interaction, erro: Exception):
    """Responde a interação com o erro e printa no console."""
    tb = traceback.format_exc()
    print(f"[PALPITES ERRO] {type(erro).__name__}: {erro}\n{tb}")
    msg = f"❌ Erro interno: `{type(erro).__name__}: {erro}`"
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)
    except Exception:
        pass


# ─── Modal ───────────────────────────────────────────────────────────────────

class PalpiteModal(discord.ui.Modal):
    placar = discord.ui.TextInput(
        label="Placar da partida",
        placeholder="Ex: Brasil 3x0 Escócia",
        max_length=40,
        required=True,
    )
    jogador_gol = discord.ui.TextInput(
        label="Jogador que vai marcar gol (opcional)",
        placeholder="Ex: Vini Jr, Rodrygo, Endrick, Raphinha...",
        max_length=40,
        required=False,
    )

    def __init__(self, cog, placar_pre: str = "", editando: bool = False):
        title = "✏️ Editar Palpite" if editando else "📊 Enviar Palpite"
        super().__init__(title=title)
        self.cog      = cog
        self.editando = editando
        if placar_pre:
            self.placar.default = placar_pre

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.cog.registrar_palpite(
                interaction,
                placar=str(self.placar).strip(),
                jogador_gol=str(self.jogador_gol).strip() or None,
                editando=self.editando,
            )
        except Exception as e:
            await _responder_erro(interaction, e)

    async def on_error(self, interaction: discord.Interaction, erro: Exception):
        await _responder_erro(interaction, erro)


# ─── View principal ───────────────────────────────────────────────────────────

class PalpitesView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="🇧🇷 Brasil 2x0 Escócia",
        style=discord.ButtonStyle.success,
        custom_id="palpite_2x0",
        row=0,
    )
    async def brasil_2x0(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.registrar_rapido(interaction, "Brasil 2x0 Escócia")
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="🔥 Brasil 3x0 Escócia",
        style=discord.ButtonStyle.success,
        custom_id="palpite_3x0",
        row=0,
    )
    async def brasil_3x0(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.registrar_rapido(interaction, "Brasil 3x0 Escócia")
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="⚽ Brasil 3x1 Escócia",
        style=discord.ButtonStyle.primary,
        custom_id="palpite_3x1",
        row=0,
    )
    async def brasil_3x1(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.registrar_rapido(interaction, "Brasil 3x1 Escócia")
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="💥 Brasil 4x0 Escócia",
        style=discord.ButtonStyle.primary,
        custom_id="palpite_4x0",
        row=0,
    )
    async def brasil_4x0(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.registrar_rapido(interaction, "Brasil 4x0 Escócia")
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="✍️ Outro Palpite",
        style=discord.ButtonStyle.secondary,
        custom_id="palpite_outro",
        row=1,
    )
    async def outro_palpite(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if jogo_ja_comecou():
                return await interaction.response.send_message(
                    "⛔ O jogo já começou! Não é mais possível enviar palpites.",
                    ephemeral=True,
                )
            await interaction.response.send_modal(PalpiteModal(self.cog))
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="✏️ Editar meu palpite",
        style=discord.ButtonStyle.secondary,
        custom_id="palpite_editar",
        row=1,
    )
    async def editar_palpite(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if jogo_ja_comecou():
                return await interaction.response.send_message(
                    "⛔ O jogo já começou! Não é possível editar palpites.",
                    ephemeral=True,
                )

            async with interaction.client.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT placar, jogador_gol FROM palpites WHERE jogo_id=$1 AND user_id=$2",
                    JOGO_ATUAL["id"], interaction.user.id,
                )

            if not row:
                return await interaction.response.send_message(
                    "📭 Você ainda não enviou um palpite neste jogo. Use os botões acima!",
                    ephemeral=True,
                )

            await interaction.response.send_modal(
                PalpiteModal(self.cog, placar_pre=row["placar"], editando=True)
            )
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="📊 Ver Ranking",
        style=discord.ButtonStyle.secondary,
        custom_id="ver_ranking",
        row=2,
    )
    async def ver_ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.mostrar_ranking(interaction)
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="🎯 Meu Palpite",
        style=discord.ButtonStyle.secondary,
        custom_id="ver_meu_palpite",
        row=2,
    )
    async def ver_meu_palpite(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.mostrar_palpite_pessoal(interaction)
        except Exception as e:
            await _responder_erro(interaction, e)


# ─── Cog ─────────────────────────────────────────────────────────────────────

class Palpites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def criar_tabela(self):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS palpites (
                    id          SERIAL PRIMARY KEY,
                    jogo_id     TEXT    NOT NULL,
                    jogo_titulo TEXT    NOT NULL,
                    user_id     BIGINT  NOT NULL,
                    user_name   TEXT    NOT NULL,
                    placar      TEXT    NOT NULL,
                    jogador_gol TEXT,
                    criado_em   TIMESTAMP DEFAULT NOW(),
                    editado_em  TIMESTAMP,
                    UNIQUE(jogo_id, user_id)
                );
            """)

    async def cog_load(self):
        await self.criar_tabela()
        self.bot.add_view(PalpitesView(self))
        print("✅ PalpitesView registrada com sucesso.")

    # ── Lógica de registro ───────────────────────────────────────────────────

    async def registrar_rapido(self, interaction: discord.Interaction, placar: str):
        if jogo_ja_comecou():
            return await interaction.response.send_message(
                "⛔ O jogo já começou! Não é mais possível enviar palpites.",
                ephemeral=True,
            )

        async with self.bot.pool.acquire() as conn:
            existe = await conn.fetchrow(
                "SELECT placar FROM palpites WHERE jogo_id=$1 AND user_id=$2",
                JOGO_ATUAL["id"], interaction.user.id,
            )

        if existe:
            return await interaction.response.send_message(
                f"⚠️ Você já enviou um palpite: **{existe['placar']}**\n"
                f"Use o botão **✏️ Editar meu palpite** para alterar.",
                ephemeral=True,
            )

        await interaction.response.send_modal(
            PalpiteModal(self, placar_pre=placar)
        )

    async def registrar_palpite(
        self,
        interaction: discord.Interaction,
        placar: str,
        jogador_gol: str | None,
        editando: bool = False,
    ):
        if jogo_ja_comecou():
            return await interaction.response.send_message(
                "⛔ O jogo já começou! Palpites encerrados.",
                ephemeral=True,
            )

        placar      = placar.strip()
        jogador_gol = jogador_gol.strip() if jogador_gol else None

        async with self.bot.pool.acquire() as conn:
            if editando:
                await conn.execute(
                    """
                    UPDATE palpites
                    SET placar=$3, jogador_gol=$4, editado_em=NOW()
                    WHERE jogo_id=$1 AND user_id=$2
                    """,
                    JOGO_ATUAL["id"], interaction.user.id, placar, jogador_gol,
                )
                acao = "atualizado"
            else:
                existe = await conn.fetchrow(
                    "SELECT id FROM palpites WHERE jogo_id=$1 AND user_id=$2",
                    JOGO_ATUAL["id"], interaction.user.id,
                )
                if existe:
                    return await interaction.response.send_message(
                        "⚠️ Você já tem um palpite registrado!\n"
                        "Use o botão **✏️ Editar meu palpite** para alterar.",
                        ephemeral=True,
                    )
                await conn.execute(
                    """
                    INSERT INTO palpites (jogo_id, jogo_titulo, user_id, user_name, placar, jogador_gol)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    JOGO_ATUAL["id"],
                    JOGO_ATUAL["titulo"],
                    interaction.user.id,
                    interaction.user.display_name,
                    placar,
                    jogador_gol,
                )
                acao = "registrado"

        embed = _embed_base(
            title=f"{'✅' if acao == 'registrado' else '✏️'} Palpite {acao} com sucesso!",
            color=COR_SUCESSO,
        )
        embed.add_field(name="⚽ Placar", value=f"**{placar}**", inline=True)
        embed.add_field(
            name="🌟 Jogador com gol",
            value=f"**{jogador_gol}**" if jogador_gol else "_Não informado_",
            inline=True,
        )

        if jogador_gol:
            embed.add_field(
                name="🏆 Categoria",
                value=(
                    f"🥇 **Combo** — placar + gol de **{jogador_gol}**\n"
                    f"Elegível para o **TOP 1** (500 seguidores Instagram) se o jogador realmente marcar!"
                ),
                inline=False,
            )
        else:
            embed.add_field(
                name="🏆 Categoria",
                value=(
                    "🥈 **Só placar** — elegível para **TOP 2** (100 seguidores Roblox)\n"
                    "💡 Dica: informe um jogador para concorrer também ao **TOP 1**!"
                ),
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Views de consulta ─────────────────────────────────────────────────────

    async def mostrar_ranking(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT placar FROM palpites WHERE jogo_id=$1",
                JOGO_ATUAL["id"],
            )

        if not rows:
            return await interaction.response.send_message(
                "📭 Ainda não há palpites registrados.",
                ephemeral=True,
            )

        contagem = Counter(r["placar"] for r in rows)
        top      = contagem.most_common(10)
        total    = len(rows)

        medals = ["🥇", "🥈", "🥉"]
        desc   = ""
        for i, (placar, votos) in enumerate(top):
            medal   = medals[i] if i < 3 else f"`{i+1}.`"
            percent = (votos / total) * 100
            barra   = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
            desc   += f"{medal} **{placar}**\n`{barra}` {votos} palpite{'s' if votos > 1 else ''} ({percent:.1f}%)\n\n"

        embed = _embed_base(
            title="📊 Ranking de Palpites",
            description=desc.strip(),
        )
        embed.add_field(name="👥 Total de participantes", value=str(total), inline=True)
        embed.add_field(name="🎯 Palpites únicos", value=str(len(contagem)), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def mostrar_palpite_pessoal(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT placar, jogador_gol, criado_em, editado_em FROM palpites WHERE jogo_id=$1 AND user_id=$2",
                JOGO_ATUAL["id"], interaction.user.id,
            )

        if not row:
            return await interaction.response.send_message(
                "📭 Você ainda não enviou um palpite neste jogo.",
                ephemeral=True,
            )

        if row["jogador_gol"]:
            categoria = f"🥇 Combo — concorre ao **TOP 1** (500 seg. Instagram) se **{row['jogador_gol']}** marcar"
        else:
            categoria = "🥈 Apenas placar — concorre ao **TOP 2** (100 seg. Roblox)"

        ts_criado  = row["criado_em"].strftime("%d/%m %H:%M")
        ts_editado = row["editado_em"].strftime("%d/%m %H:%M") if row["editado_em"] else None

        embed = _embed_base(title="🎯 Seu Palpite")
        embed.add_field(name="⚽ Placar", value=f"**{row['placar']}**", inline=True)
        embed.add_field(
            name="🌟 Jogador com gol",
            value=f"**{row['jogador_gol']}**" if row["jogador_gol"] else "_Não informado_",
            inline=True,
        )
        embed.add_field(name="🏆 Categoria", value=categoria, inline=False)
        embed.add_field(
            name="🕐 Enviado em",
            value=ts_criado + (f" _(editado {ts_editado})_" if ts_editado else ""),
            inline=False,
        )

        if not jogo_ja_comecou():
            embed.set_footer(text="Nebularis • Você ainda pode editar seu palpite antes das 19:00.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Painel de envio ───────────────────────────────────────────────────────

    @app_commands.command(
        name="palpites",
        description="Envia o painel oficial de palpites do jogo do dia.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_palpites(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🇧🇷 Brasil x Escócia 🏴󠁧󠁢󠁳󠁣󠁴󠁿",
            description=(
                "A Seleção Brasileira entra em campo e a Nebularis preparou uma premiação especial "
                "para quem acertar o placar!\n\n"
                "**Como funciona:**\n"
                "🥇 **TOP 1 — 500 seguidores no Instagram**\n"
                "└ Acertar o placar **+** indicar um jogador que vai marcar gol (e ele realmente marcar)\n\n"
                "🥈 **TOP 2 — 100 seguidores no Roblox**\n"
                "└ Acertar apenas o **placar** da partida\n\n"
                "📊 Escolha um placar nos botões abaixo ou envie o seu próprio!"
            ),
            color=COR_PRINCIPAL,
        )

        embed.add_field(name="⏰ Horário", value=f"**{JOGO_ATUAL['horario']}**", inline=True)
        embed.add_field(name="📅 Data",    value=f"**{JOGO_ATUAL['data']}**",    inline=True)
        embed.add_field(name="🏆 Competição", value=f"**{JOGO_ATUAL['competicao']}**", inline=True)
        embed.add_field(
            name="⚠️ Atenção",
            value="Palpites encerram ao início do jogo. Você pode editar enquanto não começar.",
            inline=False,
        )

        if BANNER_PALPITES_URL:
            embed.set_image(url=BANNER_PALPITES_URL)

        embed.set_footer(text="Nebularis • Um universo de grandes momentos.")

        canal = interaction.guild.get_channel(CANAL_PALPITES_ID) or interaction.channel
        await canal.send(embed=embed, view=PalpitesView(self))
        await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)

    # ── Revelar vencedores ────────────────────────────────────────────────────

    @app_commands.command(
        name="revelar_vencedores",
        description="[Admin] Revela os vencedores após inserir o placar e os jogadores que marcaram.",
    )
    @app_commands.describe(
        placar_real="Placar real da partida (ex: Brasil 3x0 Escócia)",
        jogadores_gol="Jogadores que marcaram gol, separados por vírgula (ex: Vini Jr, Rodrygo)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def revelar_vencedores(
        self,
        interaction: discord.Interaction,
        placar_real: str,
        jogadores_gol: str,
    ):
        await interaction.response.defer(ephemeral=True)

        placar_real = placar_real.strip()
        marcadores  = [j.strip().lower() for j in jogadores_gol.split(",") if j.strip()]

        async with self.bot.pool.acquire() as conn:
            todos = await conn.fetch(
                "SELECT user_id, user_name, placar, jogador_gol FROM palpites WHERE jogo_id=$1",
                JOGO_ATUAL["id"],
            )

        combos   = []
        placares = []

        for row in todos:
            acertou_placar  = row["placar"].lower() == placar_real.lower()
            acertou_jogador = False

            if row["jogador_gol"]:
                palpite_jogador = row["jogador_gol"].lower()
                acertou_jogador = any(
                    marcador in palpite_jogador or palpite_jogador in marcador
                    for marcador in marcadores
                )

            if acertou_placar and acertou_jogador:
                combos.append(row)
            elif acertou_placar:
                placares.append(row)

        marcadores_fmt = ", ".join(j.strip() for j in jogadores_gol.split(",") if j.strip())

        embed = discord.Embed(
            title="🏆 Resultado dos Palpites",
            description=(
                f"**Jogo:** {JOGO_ATUAL['titulo']}\n"
                f"**Placar real:** {placar_real}\n"
                f"**Gol(s) de:** {marcadores_fmt}"
            ),
            color=COR_OURO,
        )

        def formatar_lista(rows):
            if not rows:
                return "_Ninguém acertou_"
            return "\n".join(f"• {r['user_name']}" for r in rows[:20])

        embed.add_field(
            name="🥇 TOP 1 — Placar + jogador que marcou",
            value=f"{len(combos)} ganhador(es)\n{formatar_lista(combos)}",
            inline=False,
        )
        embed.add_field(
            name="🥈 TOP 2 — Placar exato",
            value=f"{len(placares)} ganhador(es)\n{formatar_lista(placares)}",
            inline=False,
        )
        embed.add_field(
            name="📊 Participação total",
            value=f"{len(todos)} palpites registrados",
            inline=True,
        )
        embed.set_footer(text="Nebularis • Um universo de grandes momentos.")

        canal = interaction.guild.get_channel(CANAL_PALPITES_ID) or interaction.channel
        await canal.send(embed=embed)

        dm_ok  = 0
        dm_err = 0

        async def enviar_dm(user_id: int, mensagem: str):
            nonlocal dm_ok, dm_err
            try:
                user = await interaction.client.fetch_user(user_id)
                await user.send(mensagem)
                dm_ok += 1
            except Exception:
                dm_err += 1

        for row in combos:
            await enviar_dm(
                row["user_id"],
                f"🥇 **Parabéns, {row['user_name']}!**\n\n"
                f"Você acertou o placar **{placar_real}** e o gol de **{row['jogador_gol']}** "
                f"no jogo **{JOGO_ATUAL['titulo']}**!\n\n"
                f"🏆 Você ganhou o **TOP 1 — 500 seguidores no Instagram**!\n"
                f"Aguarde o contato da equipe **Nebularis** para receber seu prêmio. 🚀"
            )

        for row in placares:
            await enviar_dm(
                row["user_id"],
                f"🥈 **Parabéns, {row['user_name']}!**\n\n"
                f"Você acertou o placar **{placar_real}** "
                f"no jogo **{JOGO_ATUAL['titulo']}**!\n\n"
                f"🏆 Você ganhou o **TOP 2 — 100 seguidores no Roblox**!\n"
                f"Aguarde o contato da equipe **Nebularis** para receber seu prêmio. 🚀"
            )

        await interaction.followup.send(
            f"✅ Resultado publicado!\n"
            f"🥇 TOP 1: {len(combos)} ganhador(es)\n"
            f"🥈 TOP 2: {len(placares)} ganhador(es)\n"
            f"📬 DMs: {dm_ok} enviadas, {dm_err} falha(s)",
            ephemeral=True,
        )

    # ── Listar palpites ───────────────────────────────────────────────────────

    @app_commands.command(
        name="listar_palpites",
        description="[Admin] Lista todos os palpites do jogo atual.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def listar_palpites(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with self.bot.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_name, placar, jogador_gol, criado_em
                FROM palpites WHERE jogo_id=$1
                ORDER BY criado_em ASC
                """,
                JOGO_ATUAL["id"],
            )

        if not rows:
            return await interaction.followup.send("📭 Nenhum palpite registrado.", ephemeral=True)

        paginas = []
        chunk   = []

        for i, row in enumerate(rows, 1):
            icone = "🌟" if row["jogador_gol"] else "⚽"
            chunk.append(
                f"`{i}.` **{row['user_name']}**\n"
                f"└ {icone} {row['placar']}"
                + (f" · {row['jogador_gol']}" if row["jogador_gol"] else "")
            )
            if len(chunk) == 15:
                paginas.append(chunk)
                chunk = []

        if chunk:
            paginas.append(chunk)

        for idx, pagina in enumerate(paginas, 1):
            embed = _embed_base(
                title=f"📋 Palpites — Página {idx}/{len(paginas)}",
                description="\n".join(pagina),
            )
            embed.set_footer(text=f"Total: {len(rows)} palpites | {JOGO_ATUAL['titulo']}")
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Palpites(bot))