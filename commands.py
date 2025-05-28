import discord
from discord.ext import commands
import random
import asyncio

class ProfileView(discord.ui.View):
    """View para o sistema de perfil interativo"""
    
    def __init__(self, target_user, bot):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.target_user = target_user
        self.bot = bot
        self.current_tab = "attributes"
    
    async def get_character_data(self):
        """Obtém dados do personagem"""
        character = await self.bot.db.get_character(self.target_user.id)
        player = await self.bot.db.get_player(self.target_user.id)
        
        if not player:
            await self.bot.db.create_player(self.target_user.id)
            player = await self.bot.db.get_player(self.target_user.id)
            
        return character, player
    
    def create_progress_bar(self, current, maximum, length=15):
        """Cria barra de progresso visual"""
        if maximum == 0:
            return "░" * length
        progress = (current / maximum)
        filled = int(progress * length)
        empty = length - filled
        return "█" * filled + "░" * empty
    
    async def create_attributes_embed(self):
        """Cria embed da aba de atributos"""
        character, player = await self.get_character_data()
        
        level = player['level']
        current_xp = player['xp']
        stat_points = player['stat_points']
        
        # Calcular XP para próximo nível
        if level == 1:
            xp_needed_next = 100
            xp_current_level = 0
        else:
            xp_needed_next = self.bot.db._xp_for_next_level(level)
            xp_current_level = self.bot.db._xp_needed_for_level(level)
        
        xp_progress = current_xp - xp_current_level
        progress_bar = self.create_progress_bar(xp_progress, xp_needed_next)
        progress_percent = (xp_progress / xp_needed_next) * 100 if xp_needed_next > 0 else 100
        
        embed = discord.Embed(
            title=f"📊 Atributos de {self.target_user.display_name}",
            color=0xff6b35
        )
        
        if character:
            faction_emoji = "👹" if character['faction'] == 'ghoul' else "🛡️"
            faction_name = "Ghoul" if character['faction'] == 'ghoul' else "Investigador CCG"
            embed.add_field(
                name="🏴 Facção",
                value=f"{faction_emoji} **{faction_name}**",
                inline=True
            )
        
        # Nível e XP
        embed.add_field(
            name="🎯 Nível",
            value=f"**{level}**",
            inline=True
        )
        
        embed.add_field(
            name="🎖️ Pontos Disponíveis",
            value=f"**{stat_points}**",
            inline=True
        )
        
        # Barra de progresso XP
        embed.add_field(
            name="📈 Progresso XP",
            value=f"```{progress_bar}```\n"
                  f"**{xp_progress:.0f}** / **{xp_needed_next}** XP ({progress_percent:.1f}%)",
            inline=False
        )
        
        # Atributos base
        if character:
            embed.add_field(
                name="💪 Atributos Principais",
                value=f"❤️ **Vida:** {character['health']}/{character['max_health']}\n"
                      f"⚡ **Vigor:** {character['stamina']}/{character['max_stamina']}\n"
                      f"💥 **Força:** {character['strength']}\n"
                      f"🏃 **Agilidade:** {character['agility']}\n"
                      f"🛡️ **Resistência:** {character['resistance']}\n"
                      f"👁️ **Percepção:** {character.get('perception', 10)}",
                inline=True
            )
            
            # Atributos específicos da facção
            if character['faction'] == 'ghoul':
                embed.add_field(
                    name="👹 Atributos Ghoul",
                    value=f"🔴 **Controle RC:** {character.get('rc_control', 10)}\n"
                          f"💚 **Regeneração:** {character.get('regeneration', 10)}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="🛡️ Atributos CCG",
                    value=f"⚔️ **Aptidão Quinque:** {character.get('quinque_aptitude', 10)}\n"
                          f"🧠 **Intelecto/Tática:** {character.get('intellect', 10)}",
                    inline=True
                )
        else:
            embed.add_field(
                name="⚠️ Personagem não criado",
                value="Use `!criar` para criar seu personagem!",
                inline=False
            )
        
        embed.set_thumbnail(url=self.target_user.display_avatar.url)
        embed.set_footer(text="Use os botões abaixo para navegar pelas abas do perfil")
        
        return embed
    
    async def create_info_embed(self):
        """Cria embed da aba de informações pessoais"""
        character, player = await self.get_character_data()
        
        embed = discord.Embed(
            title=f"👤 Informações de {self.target_user.display_name}",
            color=0x3498db
        )
        
        if character:
            embed.add_field(
                name="📝 Nome IC",
                value=character.get('ic_name', 'Não definido'),
                inline=True
            )
            
            embed.add_field(
                name="🎂 Idade",
                value=character.get('age', 'Não definido'),
                inline=True
            )
            
            embed.add_field(
                name="⚧️ Gênero/Pronomes",
                value=character.get('gender', 'Não definido'),
                inline=True
            )
            
            embed.add_field(
                name="🎨 Aparência",
                value=character.get('appearance', 'Não definido'),
                inline=False
            )
            
            embed.add_field(
                name="📖 História",
                value=character.get('backstory', 'Não definido'),
                inline=False
            )
        else:
            embed.add_field(
                name="⚠️ Personagem não criado",
                value="Use `!criar` para criar seu personagem!",
                inline=False
            )
        
        embed.set_thumbnail(url=self.target_user.display_avatar.url)
        embed.set_footer(text="Clique em 'Editar Informações' para atualizar seus dados")

        return embed
    
    async def create_abilities_embed(self):
        """Cria embed da aba de habilidades"""
        character, player = await self.get_character_data()
        
        embed = discord.Embed(
            title=f"✨ Habilidades de {self.target_user.display_name}",
            color=0x9b59b6
        )
        
        if character:
            faction = character['faction']
            if faction == 'ghoul':
                embed.add_field(
                    name="👹 Habilidades Ghoul",
                    value="• **Regeneração Acelerada** - Cura passiva\n"
                          "• **Sentidos Apurados** - Detecção de humanos\n"
                          "• **Força Sobre-humana** - Força aumentada",
                    inline=False
                )
                
                kagune = character.get('kagune_quinque', 'Não definido')
                embed.add_field(
                    name="🔴 Kagune",
                    value=f"**Tipo:** {kagune}\n"
                          "**Habilidades específicas em desenvolvimento**",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🛡️ Habilidades CCG",
                    value="• **Treinamento de Combate** - Técnicas de luta\n"
                          "• **Conhecimento de Ghouls** - Identificação\n"
                          "• **Trabalho em Equipe** - Coordenação",
                    inline=False
                )
                
                quinque = character.get('kagune_quinque', 'Não definido')
                embed.add_field(
                    name="⚔️ Quinque",
                    value=f"**Tipo:** {quinque}\n"
                          "**Habilidades específicas em desenvolvimento**",
                    inline=False
                )
        else:
            embed.add_field(
                name="⚠️ Personagem não criado",
                value="Use `!criar` para criar seu personagem!",
                inline=False
            )
        
        embed.set_thumbnail(url=self.target_user.display_avatar.url)
        embed.set_footer(text="Sistema de habilidades em expansão")
        
        return embed
    
    async def create_equipment_embed(self):
        """Cria embed da aba de equipamento"""
        character, player = await self.get_character_data()
        
        embed = discord.Embed(
            title=f"🎒 Equipamento de {self.target_user.display_name}",
            color=0xe67e22
        )
        
        if character:
            faction = character['faction']
            weapon = character.get('kagune_quinque', 'Não definido')
            
            if faction == 'ghoul':
                embed.add_field(
                    name="🔴 Kagune Principal",
                    value=f"**Tipo:** {weapon}\n"
                          f"**Rank:** A (Nível {player['level']})\n"
                          f"**Descrição:** Kagune desenvolvida através de combate",
                    inline=False
                )
                
                # Descrições dos tipos de kagune
                kagune_descriptions = {
                    'Rinkaku': '🐙 Tentáculos regenerativos com alta capacidade de cura',
                    'Ukaku': '🦅 Cristais aéreos com alta velocidade e projéteis',
                    'Koukaku': '🛡️ Armadura defensiva com alta resistência',
                    'Bikaku': '🦂 Cauda versátil com equilíbrio entre ataque e defesa'
                }
                
                if weapon in kagune_descriptions:
                    embed.add_field(
                        name="📋 Características",
                        value=kagune_descriptions[weapon],
                        inline=False
                    )
            else:
                embed.add_field(
                    name="⚔️ Quinque Principal",
                    value=f"**Tipo:** {weapon}\n"
                          f"**Rank:** B+ (Nível {player['level']})\n"
                          f"**Descrição:** Quinque forjada a partir de RC de ghoul",
                    inline=False
                )
                
                # Descrições dos tipos de quinque
                quinque_descriptions = {
                    'Espada': '⚔️ Lâmina cortante para combate corpo a corpo',
                    'Lança': '🔱 Arma de longo alcance com perfuração',
                    'Martelo': '🔨 Arma pesada com impacto devastador',
                    'Chicote': '🞭 Arma flexível para controle de área'
                }
                
                if weapon in quinque_descriptions:
                    embed.add_field(
                        name="📋 Características",
                        value=quinque_descriptions[weapon],
                        inline=False
                    )
            
            embed.add_field(
                name="🎯 Status do Equipamento",
                value=f"**Condição:** Excelente\n"
                      f"**Experiência:** {player['xp']:.0f} pontos\n"
                      f"**Upgrades:** Disponível no nível {player['level'] + 5}",
                inline=False
            )
            
        else:
            embed.add_field(
                name="⚠️ Personagem não criado",
                value="Use `!criar` para criar seu personagem!",
                inline=False
            )
        
        embed.set_thumbnail(url=self.target_user.display_avatar.url)
        embed.set_footer(text="Equipamentos evoluem conforme seu personagem cresce")
        
        return embed
    
    @discord.ui.button(label='📊 Atributos', style=discord.ButtonStyle.primary)
    async def attributes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para aba de atributos"""
        self.current_tab = "attributes"
        embed = await self.create_attributes_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='👤 Informações', style=discord.ButtonStyle.secondary)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para aba de informações"""
        self.current_tab = "info"
        embed = await self.create_info_embed()
        
        # Adicionar botão de editar informações se for o próprio usuário
        if interaction.user.id == self.target_user.id:
            edit_view = InfoEditView(self.target_user, self.bot, self)
            await interaction.response.edit_message(embed=embed, view=edit_view)
        else:
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='✨ Habilidades', style=discord.ButtonStyle.secondary)
    async def abilities_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para aba de habilidades"""
        self.current_tab = "abilities"
        embed = await self.create_abilities_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='🎒 Equipamento', style=discord.ButtonStyle.secondary)
    async def equipment_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para aba de equipamento"""
        self.current_tab = "equipment"
        embed = await self.create_equipment_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class InfoEditView(discord.ui.View):
    """View para edição de informações pessoais"""
    
    def __init__(self, target_user, bot, profile_view):
        super().__init__(timeout=300)
        self.target_user = target_user
        self.bot = bot
        self.profile_view = profile_view
    
    @discord.ui.button(label='✏️ Editar Informações', style=discord.ButtonStyle.success)
    async def edit_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para abrir modal de edição"""
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message("❌ Você só pode editar suas próprias informações!", ephemeral=True)
            return
        
        character = await self.bot.db.get_character(self.target_user.id)
        modal = InfoEditModal(self.bot, character)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='🔙 Voltar', style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para voltar ao perfil normal"""
        embed = await self.profile_view.create_info_embed()
        await interaction.response.edit_message(embed=embed, view=self.profile_view)

class InfoEditModal(discord.ui.Modal):
    """Modal para edição de informações pessoais"""
    
    def __init__(self, bot, character):
        super().__init__(title="✏️ Editar Informações do Personagem")
        self.bot = bot
        self.character = character
        
        # Campos do modal
        self.ic_name = discord.ui.TextInput(
            label="Nome IC (In-Character)",
            placeholder="Digite o nome do seu personagem...",
            default=character.get('ic_name', '') if character else '',
            max_length=50
        )
        
        self.age = discord.ui.TextInput(
            label="Idade",
            placeholder="Ex: 22 anos",
            default=character.get('age', '') if character else '',
            max_length=20
        )
        
        self.gender = discord.ui.TextInput(
            label="Gênero/Pronomes",
            placeholder="Ex: Masculino (ele/dele)",
            default=character.get('gender', '') if character else '',
            max_length=50
        )
        
        self.appearance = discord.ui.TextInput(
            label="Aparência",
            placeholder="Descreva a aparência do seu personagem...",
            default=character.get('appearance', '') if character else '',
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        
        self.backstory = discord.ui.TextInput(
            label="História Breve",
            placeholder="Conte um pouco da história do seu personagem...",
            default=character.get('backstory', '') if character else '',
            style=discord.TextStyle.paragraph,
            max_length=1000
        )
        
        # Adicionar campos ao modal
        self.add_item(self.ic_name)
        self.add_item(self.age)
        self.add_item(self.gender)
        self.add_item(self.appearance)
        self.add_item(self.backstory)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Processa o envio do modal"""
        if not self.character:
            await interaction.response.send_message("❌ Você precisa criar um personagem primeiro com `!criar`!", ephemeral=True)
            return
        
        # Atualizar informações no banco de dados
        await self.bot.db.update_character(
            interaction.user.id,
            ic_name=self.ic_name.value,
            age=self.age.value,
            gender=self.gender.value,
            appearance=self.appearance.value,
            backstory=self.backstory.value
        )
        
        embed = discord.Embed(
            title="✅ Informações Atualizadas!",
            description="Suas informações pessoais foram atualizadas com sucesso!",
            color=0x00ff88
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup_commands(bot):
    """Configura todos os comandos do bot"""
    
    @bot.command(name='perfil', aliases=['profile', 'p'])
    async def show_profile(ctx, user: discord.User = None):
        """Mostra o perfil completo e interativo do jogador"""
        if user is not None:
            target_user = user
        else:
            target_user = ctx.author
        
        # Criar view do perfil
        view = ProfileView(target_user, bot)
        
        # Criar embed inicial (atributos)
        embed = await view.create_attributes_embed()
        
        # Enviar mensagem com view
        await ctx.send(embed=embed, view=view)
    
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
    