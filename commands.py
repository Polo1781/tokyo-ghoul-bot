import discord
from discord.ext import commands
import random
import asyncio

async def setup_commands(bot):
    """Configura todos os comandos do bot"""
    
    @bot.command(name='xp')
    async def show_xp(ctx, user: discord.User = None):
        """Mostra o XP e nível do jogador"""
        target_user = user if user is not None else ctx.author
        
        player = await bot.db.get_player(target_user.id)
        if not player:
            # Criar jogador automaticamente
            await bot.db.create_player(target_user.id)
            player = await bot.db.get_player(target_user.id)
        
        level = player['level']
        current_xp = player['xp']
        stat_points = player['stat_points']
        
        # Calcular XP para próximo nível
        if level == 1:
            xp_needed_next = 100
            xp_current_level = 0
        else:
            xp_needed_next = bot.db._xp_for_next_level(level)
            xp_current_level = bot.db._xp_needed_for_level(level)
        
        xp_progress = current_xp - xp_current_level
        xp_remaining = xp_needed_next - xp_progress
        
        # Calcular porcentagem de progresso
        progress_percent = (xp_progress / xp_needed_next) * 100 if xp_needed_next > 0 else 100
        
        # Criar barra de progresso visual
        bar_length = 20
        filled_length = int((progress_percent / 100) * bar_length)
        empty_length = bar_length - filled_length
        progress_bar = "█" * filled_length + "░" * empty_length
        
        # Criar embed
        embed = discord.Embed(
            title=f"📊 Status de {target_user.display_name}",
            color=0x00ff88
        )
        
        embed.add_field(
            name="🎯 Nível",
            value=f"**{level}**",
            inline=True
        )
        
        embed.add_field(
            name="✨ XP Atual",
            value=f"**{current_xp:.1f}**",
            inline=True
        )
        
        embed.add_field(
            name="🎖️ Pontos de Status",
            value=f"**{stat_points}**",
            inline=True
        )
        
        embed.add_field(
            name="📈 Progresso para Próximo Nível",
            value=f"```{progress_bar}```\n"
                  f"**{xp_progress:.1f}** / **{xp_needed_next}** XP\n"
                  f"Restam: **{xp_remaining:.1f}** XP ({progress_percent:.1f}%)",
            inline=False
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text="🌟 Continue fazendo RP para ganhar mais XP!")
        
        await ctx.send(embed=embed)
    
    @bot.command(name='definircanalxp')
    @commands.has_permissions(administrator=True)
    async def toggle_xp_channel(ctx):
        """Ativa/desativa XP passivo no canal atual"""
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        
        is_active = await bot.db.is_xp_channel(channel_id)
        
        if is_active:
            # Remover canal
            success = await bot.db.remove_xp_channel(channel_id)
            if success:
                embed = discord.Embed(
                    title="❌ Canal de XP Desativado",
                    description=f"O canal {ctx.channel.mention} foi removido da lista de canais XP.",
                    color=0xff4444
                )
            else:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Não foi possível remover o canal.",
                    color=0xff0000
                )
        else:
            # Adicionar canal
            success = await bot.db.add_xp_channel(channel_id, guild_id)
            if success:
                embed = discord.Embed(
                    title="✅ Canal de XP Ativado",
                    description=f"O canal {ctx.channel.mention} foi adicionado à lista de canais XP.\n"
                              f"Jogadores agora ganharão XP passivo por RP neste canal!",
                    color=0x44ff44
                )
            else:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Não foi possível adicionar o canal.",
                    color=0xff0000
                )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='canaisxp')
    @commands.has_permissions(administrator=True)
    async def list_xp_channels(ctx):
        """Lista todos os canais XP do servidor"""
        channels = await bot.db.get_xp_channels(ctx.guild.id)
        
        if not channels:
            embed = discord.Embed(
                title="📋 Canais XP",
                description="Nenhum canal de XP configurado neste servidor.",
                color=0xffaa00
            )
        else:
            channel_mentions = []
            for channel_id in channels:
                channel = bot.get_channel(channel_id)
                if channel:
                    channel_mentions.append(channel.mention)
                else:
                    channel_mentions.append(f"Canal ID: {channel_id} (não encontrado)")
            
            embed = discord.Embed(
                title="📋 Canais XP Ativos",
                description="\n".join(channel_mentions),
                color=0x00ff88
            )
            embed.set_footer(text=f"Total: {len(channels)} canais")
        
        await ctx.send(embed=embed)
