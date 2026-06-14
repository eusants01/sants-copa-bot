import discord
from discord.ext import commands, tasks
from datetime import datetime


CANAL_COPA_ID = 0
MENSAGEM_ID = 0


class PainelCopa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.atualizar_painel.start()

    def criar_embed(self):
        embed = discord.Embed(
            title="🏆 Sants Copa",
            description="☠️ **Central oficial da Copa na Família Sant's**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="⚽ Jogos de Hoje",
            value=(
                "🇧🇷 Brasil x Escócia — 16:00\n"
                "🇦🇷 Argentina x Egito — 19:00\n"
                "🇫🇷 França x Senegal — 22:00"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 Sistemas",
            value=(
                "🏆 Palpites\n"
                "📊 Ranking\n"
                "⚽ Jogos\n"
                "🇧🇷 Rumo ao Hexa"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Atualizado automaticamente • {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        )

        return embed

    @commands.command(name="painelcopa")
    @commands.has_permissions(administrator=True)
    async def painelcopa(self, ctx):
        embed = self.criar_embed()
        msg = await ctx.send(embed=embed)

        await ctx.send(
            f"✅ Painel criado com sucesso!\n"
            f"ID da mensagem: `{msg.id}`\n\n"
            f"Agora coloque esse ID em `MENSAGEM_ID` no arquivo `painel.py`."
        )

    @tasks.loop(minutes=10)
    async def atualizar_painel(self):
        await self.bot.wait_until_ready()

        if CANAL_COPA_ID == 0 or MENSAGEM_ID == 0:
            return

        canal = self.bot.get_channel(CANAL_COPA_ID)

        if canal is None:
            return

        try:
            mensagem = await canal.fetch_message(MENSAGEM_ID)
            await mensagem.edit(embed=self.criar_embed())
            print("✅ Painel da Copa atualizado.")
        except Exception as e:
            print(f"❌ Erro ao atualizar painel: {e}")


async def setup(bot):
    await bot.add_cog(PainelCopa(bot))