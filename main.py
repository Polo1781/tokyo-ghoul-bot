import discord
from discord.ext import commands
import os
import logging
from database import Database
from commands import setup_commands

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class TokyoGhoulBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='The System 🥀 - Bot de combate PvP temático de Tokyo Ghoul'
        )
        
        self.db = Database()
    
    async def setup_hook(self):
        """Configuração inicial do bot"""
        await self.db.initialize()
        await setup_commands(self)
        logging.info("Bot configurado com sucesso!")
    
    async def on_ready(self):
        """Evento chamado quando o bot está pronto"""
        logging.info(f'{self.user} conectou ao Discord!')
        logging.info(f'Bot está em {len(self.guilds)} servidores')
        
        # Definir atividade do bot
        activity = discord.Game(name="Sistema XP | !xp")
        await self.change_presence(activity=activity)
    
    async def on_message(self, message):
        """Evento chamado quando uma mensagem é enviada"""
        # Processar comandos primeiro
        await self.process_commands(message)
        
        # Ignorar bots e comandos
        if message.author.bot or message.content.startswith('!'):
            return
        
        # Verificar se é um canal XP
        is_xp_channel = await self.db.is_xp_channel(message.channel.id)
        if not is_xp_channel:
            return
        
        # Verificar se a mensagem tem pelo menos 10 caracteres (para evitar spam)
        if len(message.content.strip()) < 10:
            return
        
        # Gerar XP aleatório entre 0.5 e 3.0
        import random
        xp_gained = round(random.uniform(0.5, 3.0), 1)
        
        # Adicionar XP ao jogador
        leveled_up, old_level, new_level, stat_points_gained = await self.db.add_xp(message.author.id, xp_gained)
        
        # Se subiu de nível, enviar notificação
        if leveled_up:
            await self.send_level_up_notification(message.author, old_level, new_level, stat_points_gained, message.channel)
    
    async def send_level_up_notification(self, user, old_level, new_level, stat_points_gained, channel):
        """Envia notificação de level up"""
        embed = discord.Embed(
            title="🌟 LEVEL UP! 🌟",
            description=f"**{user.display_name}** subiu para o nível **{new_level}**!",
            color=0xffd700
        )
        
        embed.add_field(
            name="📈 Progressão",
            value=f"Nível {old_level} → Nível {new_level}",
            inline=True
        )
        
        embed.add_field(
            name="🎖️ Recompensas",
            value=f"**+{stat_points_gained}** Pontos de Status",
            inline=True
        )
        
        embed.add_field(
            name="💡 Dica",
            value="Use seus pontos de status sabiamente para fortalecer seu personagem!",
            inline=False
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Parabéns pelo seu progresso!")
        
        await channel.send(embed=embed)
    
    async def on_command_error(self, ctx, error):
        """Tratamento de erros de comandos"""
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="❌ Comando não encontrado",
                description="Use `!xp` para ver seu status ou peça ajuda a um administrador.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Argumentos insuficientes",
                description=f"Comando incompleto. Verifique como usar o comando corretamente.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Comando em cooldown",
                description=f"Aguarde {error.retry_after:.1f} segundos antes de usar este comando novamente.",
                color=0xffaa00
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="🚫 Sem Permissão",
                description="Você precisa ser um **Administrador** para usar este comando.\n"
                          "Apenas administradores podem configurar canais de XP.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="🚫 Acesso Negado",
                description="Você não tem permissão para usar este comando.\n"
                          "Este comando é restrito a administradores.",
                color=0xff4444
            )
            await ctx.send(embed=embed)
        else:
            logging.error(f"Erro não tratado: {error}")
            embed = discord.Embed(
                title="💥 Erro interno",
                description="Ocorreu um erro inesperado. Tente novamente em alguns momentos.",
                color=0xff0000
            )
            await ctx.send(embed=embed)

def main():
    """Função principal para iniciar o bot"""
    # Obter token do Discord das variáveis de ambiente
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logging.error("Token do Discord não encontrado! Configure a variável DISCORD_TOKEN")
        return
    
    # Criar e executar o bot
    bot = TokyoGhoulBot()
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logging.error("Token inválido! Verifique o token do Discord.")
    except Exception as e:
        logging.error(f"Erro ao iniciar o bot: {e}")

if __name__ == "__main__":
    main()
