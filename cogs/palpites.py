import os
import discord
import traceback

from datetime import datetime
from discord.ext import commands
from discord import app_commands
from collections import Counter
from zoneinfo import ZoneInfo


CANAL_PALPITES_ID = int(os.getenv("CANAL_PALPITES_ID", 0))

BANNER_PALPITES_URL = os.getenv(
    "BANNER_PALPITES_URL",
    "https://cdn.discordapp.com/attachments/961677475191078992/1520210401151684779/image.png?ex=6a405dc3&is=6a3f0c43&hm=ca81f07a4d8eaa99f4fc5371c4fb17f2d3a6aae41ced4a19b7b0715306a274aa&"
)

FUSO = ZoneInfo("America/Sao_Paulo")

JOGO_ATUAL = {
    "id":         "brasil_japao_2026",
    "titulo":     "Brasil x Japão",
    "horario":    "14:00",
    "data":       "29/06",
    "competicao": "Copa do Mundo 2026",
    "inicio":     datetime(2026, 6, 29, 14, 0, tzinfo=FUSO),
}

COR_PRINCIPAL = 0x7B4FDB
COR_OURO      = 0xFFD700
COR_SUCESSO   = 0x43B581
COR_ERRO      = 0xFF4C4C


# ─── Helpers ──────────────────────────────────────────────────────────────────

def jogo_ja_comecou() -> bool:
    return datetime.now(tz=FUSO) >= JOGO_ATUAL["inicio"]


def _embed_base(title: str, description: str = "", color: int = COR_PRINCIPAL) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Nebularis • Um universo de grandes momentos.")
    return embed


async def _responder_erro(interaction: discord.Interaction, erro: Exception):
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


# ─── Modais ───────────────────────────────────────────────────────────────────

class PalpiteModal(discord.ui.Modal):
    placar = discord.ui.TextInput(
        label="⚽ Placar da partida",
        placeholder="Ex: Brasil 3x0 Japão",
        max_length=40,
        required=True,
    )
    jogador_gol = discord.ui.TextInput(
        label="🌟 Jogador que vai marcar gol (opcional)",
        placeholder="Ex: Vini Jr, Endrick, Raphinha... (concorre ao TOP 1)",
        max_length=40,
        required=False,
    )

    def __init__(self, cog, placar_pre: str = "", jogador_pre: str = "", editando: bool = False):
        super().__init__(title="✏️ Editar Palpite" if editando else "🎯 Enviar Palpite")
        self.cog      = cog
        self.editando = editando
        if placar_pre:
            self.placar.default = placar_pre
        if jogador_pre:
            self.jogador_gol.default = jogador_pre

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.cog.registrar_palpite(
                interaction=interaction,
                placar=str(self.placar).strip(),
                jogador_gol=str(self.jogador_gol).strip() or None,
                editando=self.editando,
            )
        except Exception as e:
            await _responder_erro(interaction, e)

    async def on_error(self, interaction: discord.Interaction, erro: Exception):
        await _responder_erro(interaction, erro)


class VencedoresModal(discord.ui.Modal, title="🏆 Revelar Resultado"):
    placar_real = discord.ui.TextInput(
        label="Placar final da partida",
        placeholder="Ex: Brasil 3x0 Japão",
        max_length=40,
        required=True,
    )
    jogadores_gol = discord.ui.TextInput(
        label="Jogadores que marcaram (separados por vírgula)",
        placeholder="Ex: Vini Jr, Endrick, Raphinha",
        max_length=150,
        required=True,
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.cog.processar_vencedores(
                interaction=interaction,
                placar_real=str(self.placar_real).strip(),
                jogadores_gol=str(self.jogadores_gol).strip(),
            )
        except Exception as e:
            await _responder_erro(interaction, e)

    async def on_error(self, interaction: discord.Interaction, erro: Exception):
        await _responder_erro(interaction, erro)


# ─── View ─────────────────────────────────────────────────────────────────────

class PalpitesView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    # ── Linha 0: ações principais ─────────────────────────────────────────────

    @discord.ui.button(
        label="Enviar Palpite",
        emoji="🎯",
        style=discord.ButtonStyle.success,
        custom_id="palpite_enviar",
        row=0,
    )
    async def enviar_palpite(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if jogo_ja_comecou():
                return await interaction.response.send_message(
                    "⛔ O jogo já começou! Palpites encerrados.", ephemeral=True
                )

            async with interaction.client.pool.acquire() as conn:
                existe = await conn.fetchrow(
                    "SELECT placar FROM palpites WHERE jogo_id=$1 AND user_id=$2",
                    JOGO_ATUAL["id"], interaction.user.id,
                )

            if existe:
                return await interaction.response.send_message(
                    f"⚠️ Você já tem um palpite registrado: **{existe['placar']}**\n"
                    "Use o botão **✏️ Editar Palpite** para alterar.",
                    ephemeral=True,
                )

            await interaction.response.send_modal(PalpiteModal(self.cog))
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="Editar Palpite",
        emoji="✏️",
        style=discord.ButtonStyle.primary,
        custom_id="palpite_editar",
        row=0,
    )
    async def editar_palpite(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if jogo_ja_comecou():
                return await interaction.response.send_message(
                    "⛔ O jogo já começou! Não é possível editar palpites.", ephemeral=True
                )

            async with interaction.client.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT placar, jogador_gol FROM palpites WHERE jogo_id=$1 AND user_id=$2",
                    JOGO_ATUAL["id"], interaction.user.id,
                )

            if not row:
                return await interaction.response.send_message(
                    "📭 Você ainda não enviou um palpite. Use o botão **🎯 Enviar Palpite**!",
                    ephemeral=True,
                )

            await interaction.response.send_modal(
                PalpiteModal(
                    self.cog,
                    placar_pre=row["placar"],
                    jogador_pre=row["jogador_gol"] or "",
                    editando=True,
                )
            )
        except Exception as e:
            await _responder_erro(interaction, e)


    @discord.ui.button(
        label="Meu Palpite",
        emoji="🎯",
        style=discord.ButtonStyle.secondary,
        custom_id="ver_meu_palpite",
        row=1,
    )
    async def ver_meu_palpite(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.mostrar_palpite_pessoal(interaction)
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="Ranking",
        emoji="📊",
        style=discord.ButtonStyle.secondary,
        custom_id="ver_ranking",
        row=1,
    )
    async def ver_ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.mostrar_ranking(interaction)
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="Participantes",
        emoji="👥",
        style=discord.ButtonStyle.secondary,
        custom_id="ver_participantes",
        row=1,
    )
    async def ver_participantes(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.cog.mostrar_participantes(interaction)
        except Exception as e:
            await _responder_erro(interaction, e)

    @discord.ui.button(
        label="Revelar Vencedores",
        emoji="🏆",
        style=discord.ButtonStyle.danger,
        custom_id="revelar_vencedores_btn",
        row=2,
    )
    async def revelar_vencedores_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    "⛔ Apenas adm podem usar isso baby rsrs.", ephemeral=True
                )
            await interaction.response.send_modal(VencedoresModal(self.cog))
        except Exception as e:
            await _responder_erro(interaction, e)


# ─── Cog ──────────────────────────────────────────────────────────────────────

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
            # Migration segura: renomeia coluna antiga se ainda existir
            await conn.execute("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='palpites' AND column_name='palpite'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='palpites' AND column_name='placar'
                    ) THEN
                        ALTER TABLE palpites RENAME COLUMN palpite TO placar;
                    END IF;
                END $$;
            """)
            await conn.execute("ALTER TABLE palpites ADD COLUMN IF NOT EXISTS jogador_gol TEXT;")
            await conn.execute("ALTER TABLE palpites ADD COLUMN IF NOT EXISTS editado_em TIMESTAMP;")

    async def cog_load(self):
        await self.criar_tabela()
        self.bot.add_view(PalpitesView(self))
        print("✅ Sistema de palpites carregado.")

    # ── Registro ──────────────────────────────────────────────────────────────

    async def registrar_palpite(
        self,
        interaction: discord.Interaction,
        placar: str,
        jogador_gol: str | None,
        editando: bool = False,
    ):
        if jogo_ja_comecou():
            return await interaction.response.send_message(
                "⛔ O jogo já começou! Palpites encerrados.", ephemeral=True
            )

        placar      = placar.strip()
        jogador_gol = jogador_gol.strip() if jogador_gol else None

        async with self.bot.pool.acquire() as conn:
            if editando:
                resultado = await conn.execute(
                    "UPDATE palpites SET placar=$3, jogador_gol=$4, editado_em=NOW() WHERE jogo_id=$1 AND user_id=$2",
                    JOGO_ATUAL["id"], interaction.user.id, placar, jogador_gol,
                )
                # Se não atualizou nenhuma linha, o palpite não existe ainda
                if resultado == "UPDATE 0":
                    return await interaction.response.send_message(
                        "📭 Você ainda não tem um palpite para editar. Use **🎯 Enviar Palpite**!",
                        ephemeral=True,
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
                        "Use o botão **✏️ Editar Palpite** para alterar.",
                        ephemeral=True,
                    )
                await conn.execute(
                    """
                    INSERT INTO palpites (jogo_id, jogo_titulo, user_id, user_name, placar, jogador_gol)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    JOGO_ATUAL["id"], JOGO_ATUAL["titulo"],
                    interaction.user.id, interaction.user.display_name,
                    placar, jogador_gol,
                )
                acao = "registrado"

        # ── Confirmação ───────────────────────────────────────────────────────
        icone = "✅" if acao == "registrado" else "✏️"

        embed = _embed_base(
            title=f"{icone} Palpite {acao}!",
            color=COR_SUCESSO,
        )
        embed.add_field(name="⚽ Placar", value=f"**{placar}**", inline=True)
        embed.add_field(
            name="🌟 Jogador",
            value=f"**{jogador_gol}**" if jogador_gol else "_Não informado_",
            inline=True,
        )

        if jogador_gol:
            embed.add_field(
                name="🏆 Categoria",
                value=(
                    f"🥇 **Combo** — você chutou o placar e o gol de **{jogador_gol}**\n"
                    "Se ele realmente marcar, você concorre ao **TOP 1**!"
                ),
                inline=False,
            )
        else:
            embed.add_field(
                name="🏆 Categoria",
                value=(
                    "🥈 **Placar** — você concorre ao **TOP 2**\n"
                    "💡 Informe um jogador para concorrer também ao **TOP 1**!"
                ),
                inline=False,
            )

        if not jogo_ja_comecou():
            embed.set_footer(
                text=f"Nebularis • Você pode editar até às {JOGO_ATUAL['horario']} do dia {JOGO_ATUAL['data']}."
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Ranking ───────────────────────────────────────────────────────────────

    async def mostrar_ranking(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT placar FROM palpites WHERE jogo_id=$1", JOGO_ATUAL["id"]
            )

        if not rows:
            return await interaction.response.send_message(
                "📭 Ainda não há palpites registrados.", ephemeral=True
            )

        contagem = Counter(r["placar"] for r in rows)
        top      = contagem.most_common(10)
        total    = len(rows)
        medals   = ["🥇", "🥈", "🥉"]
        desc     = ""

        for i, (placar, votos) in enumerate(top):
            medal   = medals[i] if i < 3 else f"`{i+1}.`"
            percent = (votos / total) * 100
            filled  = int(percent / 10)
            barra   = "█" * filled + "░" * (10 - filled)
            desc   += f"{medal} **{placar}**\n`{barra}` {votos} voto{'s' if votos > 1 else ''} ({percent:.1f}%)\n\n"

        embed = _embed_base(
            title="📊 Ranking de Palpites",
            description=desc.strip(),
        )
        embed.add_field(name="👥 Participantes", value=f"**{total}**", inline=True)
        embed.add_field(name="🎯 Placares únicos", value=f"**{len(contagem)}**", inline=True)

        # Palpite mais popular em destaque
        mais_popular, qtd = top[0]
        embed.add_field(
            name="🔥 Favorito da galera",
            value=f"**{mais_popular}** com {qtd} voto{'s' if qtd > 1 else ''}",
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


    async def mostrar_palpite_pessoal(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT placar, jogador_gol, criado_em, editado_em FROM palpites WHERE jogo_id=$1 AND user_id=$2",
                JOGO_ATUAL["id"], interaction.user.id,
            )

        if not row:
            return await interaction.response.send_message(
                "📭 Você ainda não enviou um palpite.\nUse o botão **🎯 Enviar Palpite**!",
                ephemeral=True,
            )

        categoria = (
            f"🥇 **Combo** — concorre ao TOP 1 se **{row['jogador_gol']}** marcar"
            if row["jogador_gol"] else
            "🥈 **Placar** — concorre ao TOP 2"
        )
        ts_criado  = row["criado_em"].strftime("%d/%m às %H:%M")
        ts_editado = row["editado_em"].strftime("%d/%m às %H:%M") if row["editado_em"] else None

        embed = _embed_base(title="🎯 Seu Palpite")
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="⚽ Placar", value=f"**{row['placar']}**", inline=True)
        embed.add_field(
            name="🌟 Jogador",
            value=f"**{row['jogador_gol']}**" if row["jogador_gol"] else "_Não informado_",
            inline=True,
        )
        embed.add_field(name="🏆 Categoria", value=categoria, inline=False)
        embed.add_field(
            name="🕐 Histórico",
            value=f"Enviado em {ts_criado}" + (f"\nEditado em {ts_editado}" if ts_editado else ""),
            inline=False,
        )

        if not jogo_ja_comecou():
            embed.set_footer(
                text=f"Nebularis • Você pode editar até às {JOGO_ATUAL['horario']} do dia {JOGO_ATUAL['data']}."
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Lista de participantes ────────────────────────────────────────────────

    async def mostrar_participantes(self, interaction: discord.Interaction):
        async with self.bot.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_name, jogador_gol, criado_em
                FROM palpites
                WHERE jogo_id=$1
                ORDER BY criado_em ASC
                """,
                JOGO_ATUAL["id"],
            )

        if not rows:
            return await interaction.response.send_message(
                "📭 Nenhum participante ainda.", ephemeral=True
            )

        total_combo  = sum(1 for r in rows if r["jogador_gol"])
        total_placar = len(rows) - total_combo

        nomes = ""
        for i, row in enumerate(rows, 1):
            icone = "🌟" if row["jogador_gol"] else "⚽"
            nomes += f"`{i}.` {icone} **{row['user_name']}**\n"
            if i >= 30:
                nomes += f"_...e mais {len(rows) - 30} participante(s)_\n"
                break

        embed = _embed_base(
            title="👥 Participantes",
            description=nomes.strip(),
        )
        embed.add_field(name="📊 Total", value=f"**{len(rows)}** participantes", inline=True)
        embed.add_field(name="🥇 Com jogador", value=f"**{total_combo}** combos", inline=True)
        embed.add_field(name="🥈 Só placar", value=f"**{total_placar}** palpites", inline=True)
        embed.set_footer(text="Nebularis • 🌟 = informou jogador | ⚽ = só placar")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Processar vencedores ──────────────────────────────────────────────────

    async def processar_vencedores(
        self,
        interaction: discord.Interaction,
        placar_real: str,
        jogadores_gol: str,
    ):
        await interaction.response.defer(ephemeral=True)

        marcadores = [j.strip().lower() for j in jogadores_gol.split(",") if j.strip()]

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

        def mencoes(rows) -> str:
            if not rows:
                return "_Ninguém acertou_ 😔"
            return "\n".join(f"• <@{r['user_id']}>" for r in rows[:20])

        # ── Embed público ─────────────────────────────────────────────────────
        embed = discord.Embed(
            title="🏆 Resultado dos Palpites!",
            description=(
                f"O apito final soou! Confira quem acertou.\n\n"
                f"> `🏟️` **Jogo:** {JOGO_ATUAL['titulo']}\n"
                f"> `⚽` **Placar final:** `{placar_real}`\n"
                f"> `🌟` **Gol(s) de:** {marcadores_fmt}"
            ),
            color=COR_OURO,
        )
        embed.add_field(
            name="> `🥇` TOP 1 — 500 seguidores no Instagram",
            value=f"Acertaram placar + jogador:\n{mencoes(combos)}",
            inline=False,
        )
        embed.add_field(
            name="> `🥈` TOP 2 — 100 seguidores no Roblox",
            value=f"Acertaram o placar:\n{mencoes(placares)}",
            inline=False,
        )
        embed.add_field(name="👥 Participantes", value=f"**{len(todos)}**", inline=True)
        embed.add_field(name="🥇 TOP 1", value=f"**{len(combos)}** ganhador(es)", inline=True)
        embed.add_field(name="🥈 TOP 2", value=f"**{len(placares)}** ganhador(es)", inline=True)

        if combos or placares:
            embed.add_field(
                name="📬 Próximos passos",
                value="Os vencedores receberão um contato da equipe **Nebularis** em breve. Parabéns! 🚀",
                inline=False,
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
                f"Aguarde o contato da equipe **Nebularis**. 🚀"
            )

        for row in placares:
            await enviar_dm(
                row["user_id"],
                f"🥈 **Parabéns, {row['user_name']}!**\n\n"
                f"Você acertou o placar **{placar_real}** "
                f"no jogo **{JOGO_ATUAL['titulo']}**!\n\n"
                f"🏆 Você ganhou o **TOP 2 — 100 seguidores no Roblox**!\n"
                f"Aguarde o contato da equipe **Nebularis**. 🚀"
            )

        await interaction.followup.send(
            f"✅ Resultado anunciado!\n"
            f"🥇 TOP 1: {len(combos)} ganhador(es)\n"
            f"🥈 TOP 2: {len(placares)} ganhador(es)\n"
            f"📬 DMs: {dm_ok} enviadas, {dm_err} falha(s)",
            ephemeral=True,
        )

    @app_commands.command(name="palpites", description="Envia o painel oficial de palpites do jogo do dia.")
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_palpites(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🇧🇷 Brasil x Japão 🇯🇵",
            description=(
                "A Seleção Brasileira entra em campo pela **Copa do Mundo 2026** "
                "e a Nebularis preparou uma premiação especial para quem acertar o placar!\n\n"
                "**Como participar:**\n"
                "Clique em **🎯 Enviar Palpite**, informe o placar e, se quiser concorrer ao TOP 1, "
                "informe também o jogador que vai marcar gol.\n\n"
                "**Premiação:**\n"
                "🥇 **TOP 1 — 500 seguidores no Instagram**\n"
                "└ Acertar o placar **+** um jogador que vai marcar gol\n\n"
                "🥈 **TOP 2 — 100 seguidores no Roblox**\n"
                "└ Acertar apenas o **placar** da partida"
            ),
            color=COR_PRINCIPAL,
        )
        embed.add_field(name="📅 Data",      value=f"**{JOGO_ATUAL['data']}**",    inline=True)
        embed.add_field(name="⏰ Horário",   value=f"**{JOGO_ATUAL['horario']}**", inline=True)
        embed.add_field(name="🏆 Competição", value=f"**{JOGO_ATUAL['competicao']}**", inline=True)
        embed.add_field(
            name="⚠️ Importante",
            value=(
                f"Palpites encerram às **{JOGO_ATUAL['horario']}** do dia **{JOGO_ATUAL['data']}**.\n"
                "Você pode editar seu palpite quantas vezes quiser antes do apito inicial."
            ),
            inline=False,
        )
        if BANNER_PALPITES_URL:
            embed.set_image(url=BANNER_PALPITES_URL)
        embed.set_footer(text="Nebularis • Um universo de grandes momentos.")

        canal = interaction.guild.get_channel(CANAL_PALPITES_ID) or interaction.channel
        await canal.send(embed=embed, view=PalpitesView(self))
        await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)

    # ── Slash: listar palpites (admin) ────────────────────────────────────────

    @app_commands.command(name="listar_palpites", description="[Admin] Lista todos os palpites do jogo atual.")
    @app_commands.checks.has_permissions(administrator=True)
    async def listar_palpites(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with self.bot.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_name, placar, jogador_gol, criado_em FROM palpites WHERE jogo_id=$1 ORDER BY criado_em ASC",
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
                + (f" · _{row['jogador_gol']}_" if row["jogador_gol"] else "")
            )
            if len(chunk) == 15:
                paginas.append(chunk)
                chunk = []

        if chunk:
            paginas.append(chunk)

        for idx, pagina in enumerate(paginas, 1):
            embed = _embed_base(
                title=f"📋 Palpites — {idx}/{len(paginas)}",
                description="\n".join(pagina),
            )
            embed.set_footer(text=f"{len(rows)} palpites no total | {JOGO_ATUAL['titulo']} | 🌟 = informou jogador")
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="revelar_vencedores", description="[Admin] Revela os vencedores dos palpites.")
    @app_commands.describe(
        placar_real="Placar real da partida. Ex: Brasil 3x0 Japão",
        jogadores_gol="Jogadores que marcaram gol, separados por vírgula. Ex: Vini Jr, Endrick",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def revelar_vencedores(self, interaction: discord.Interaction, placar_real: str, jogadores_gol: str):
        await self.processar_vencedores(interaction, placar_real.strip(), jogadores_gol.strip())


async def setup(bot):
    await bot.add_cog(Palpites(bot))