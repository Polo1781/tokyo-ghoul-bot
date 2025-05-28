import discord
from discord import ui
import random

# Supondo que você terá FAMILIAS_GHOUL, FAMILIAS_CCG, etc. no seu config.py
# from config import FAMILIAS_GHOUL, FAMILIAS_CCG, HABILIDADES_INICIAIS_GHOUL, HABILIDADES_INICIAIS_CCG

# Esta classe é um exemplo de como você guardaria os dados durante o processo de criação
# Você pode adaptar para passar um objeto de dados entre as views
class CreationState:
    def __init__(self, author_id, bot_instance):
        self.author_id = author_id
        self.bot = bot_instance
        self.faction = None
        self.family_options = [] # Armazena as 3 famílias roladas
        self.chosen_family_data = None # Armazena a família escolhida com seus bônus
        self.initial_ability_options = []
        self.chosen_initial_ability_data = None
        self.character_name_ic = None
        self.age = None
        self.gender = None
        self.appearance = None
        self.backstory = None
        self.message_to_edit = None # Para editar a mensagem original com novas views

    def get_family_list_for_faction(self):
        # Esta função buscaria de config.py
        # Exemplo simplificado:
        if self.faction == "ghoul":
            # return FAMILIAS_GHOUL # Do seu config.py
            return { 
                "Comum": [{"nome": "Rato de Beco", "bonus": {"strength": 1, "agility": 2}, "raridade": "Comum", "descricao": "Ágil e furtivo."}],
                "Rara": [{"nome": "Filho da Escuridão", "bonus": {"strength": 2, "rc_control": 1}, "raridade": "Rara", "descricao": "Afinidade com células RC."}]
            } # Placeholder
        elif self.faction == "ccg":
            # return FAMILIAS_CCG
            return {
                "Comum": [{"nome": "Cadete Promissor", "bonus": {"resistance": 1, "perception": 2}, "raridade": "Comum", "descricao": "Olhar atento e resiliente."}],
                "Rara": [{"nome": "Herdeiro do Dever", "bonus": {"intellect": 2, "quinque_aptitude": 1}, "raridade": "Rara", "descricao": "Tradição na CCG."}]
            } # Placeholder
        return {}

    def get_initial_ability_list_for_faction(self):
        # Esta função buscaria de config.py
        if self.faction == "ghoul":
            # return HABILIDADES_INICIAIS_GHOUL
            return [{"nome": "Garra Afiada", "tipo": "Rinkaku Leve", "descricao": "Um ataque rápido com uma pequena garra."}, {"nome": "Disparo de Estilhaços", "tipo": "Ukaku Rudimentar", "descricao": "Dispara pequenos estilhaços RC."}] # Placeholder
        elif self.faction == "ccg":
            # return HABILIDADES_INICIAIS_CCG
            return [{"nome": "Corte Preciso", "tipo": "Quinque Leve (Lâmina)", "descricao": "Um golpe rápido com uma quinque padrão."}, {"nome": "Postura Defensiva", "tipo": "Técnica CCG", "descricao": "Aumenta a defesa temporariamente."}] # Placeholder
        return []

# --- MODAL PARA INFORMAÇÕES PESSOAIS ---
class CharacterInfoModal(ui.Modal, title="📝 Detalhes do Personagem"):
    def __init__(self, creation_state: CreationState):
        super().__init__()
        self.creation_state = creation_state

        self.ic_name = ui.TextInput(label="Nome do Personagem (IC)", placeholder="Seu nome no jogo...", max_length=50)
        self.age = ui.TextInput(label="Idade", placeholder="Ex: 22", max_length=10)
        self.gender = ui.TextInput(label="Gênero/Pronomes", placeholder="Ex: Masculino (ele/dele)", max_length=50)
        self.appearance = ui.TextInput(label="Aparência", placeholder="Descreva ou coloque um link de imagem...", style=discord.TextStyle.paragraph, max_length=300)
        self.backstory = ui.TextInput(label="História Breve", placeholder="Conte um pouco sobre seu personagem...", style=discord.TextStyle.paragraph, max_length=1000)

        self.add_item(self.ic_name)
        self.add_item(self.age)
        self.add_item(self.gender)
        self.add_item(self.appearance)
        self.add_item(self.backstory)

    async def on_submit(self, interaction: discord.Interaction):
        self.creation_state.character_name_ic = self.ic_name.value
        self.creation_state.age = self.age.value
        self.creation_state.gender = self.gender.value
        self.creation_state.appearance = self.appearance.value
        self.creation_state.backstory = self.backstory.value

        await interaction.response.defer() # Adia a resposta para a próxima view
        
        confirmation_view = ConfirmationView(self.creation_state)
        embed = await confirmation_view.create_confirmation_embed()
        if self.creation_state.message_to_edit:
            await self.creation_state.message_to_edit.edit(embed=embed, view=confirmation_view)
        else: # Fallback
            self.creation_state.message_to_edit = await interaction.followup.send(embed=embed, view=confirmation_view, ephemeral=False)


# --- VIEW DE CONFIRMAÇÃO FINAL ---
class ConfirmationView(ui.View):
    def __init__(self, creation_state: CreationState):
        super().__init__(timeout=300)
        self.creation_state = creation_state

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.creation_state.author_id:
            await interaction.response.send_message("Estes botões não são para você!", ephemeral=True)
            return False
        return True

    async def create_confirmation_embed(self):
        embed = discord.Embed(title="⭐ Revisão Final do Personagem ⭐", color=0x00ff00)
        embed.description = (
            f"**Facção:** {self.creation_state.faction.capitalize() if self.creation_state.faction else 'Não escolhida'}\n"
            f"**Família:** {self.creation_state.chosen_family_data['nome'] if self.creation_state.chosen_family_data else 'Não escolhida'} (Raridade: {self.creation_state.chosen_family_data['raridade'] if self.creation_state.chosen_family_data else 'N/A'})\n"
            f"  *Bônus:* {self.creation_state.chosen_family_data['bonus'] if self.creation_state.chosen_family_data else 'N/A'}\n"
            f"**Habilidade/Arma Inicial:** {self.creation_state.chosen_initial_ability_data['nome'] if self.creation_state.chosen_initial_ability_data else 'Não escolhida'} ({self.creation_state.chosen_initial_ability_data['tipo'] if self.creation_state.chosen_initial_ability_data else 'N/A'})\n\n"
            f"**Nome IC:** {self.creation_state.character_name_ic or '*Não definido*'}\n"
            f"**Idade:** {self.creation_state.age or '*Não definido*'}\n"
            f"**Gênero/Pronomes:** {self.creation_state.gender or '*Não definido*'}\n"
            f"**Aparência:** {self.creation_state.appearance or '*Não definido*'}\n"
            f"**História:** {self.creation_state.backstory or '*Não definido*'}\n"
        )
        embed.set_footer(text="Confirme para criar seu personagem ou cancele para recomeçar.")
        return embed

    @ui.button(label="✅ Confirmar Criação", style=discord.ButtonStyle.success, custom_id="confirm_creation_final")
    async def confirm_button(self, interaction: discord.Interaction, button: ui.Button):
        # --- LÓGICA DE CRIAÇÃO FINAL NO BANCO DE DADOS ---
        # 1. Pegar todos os dados de self.creation_state
        # 2. Calcular atributos base + bônus da família
        # 3. Chamar self.creation_state.bot.db.create_character(...) com todos os dados
        
        # Exemplo simplificado de dados para o DB (você precisa expandir isso)
        base_attrs = {"strength": 10, "agility": 10, "resistance": 10, "health": 100, "max_health": 100, "stamina": 50, "max_stamina": 50, "perception": 10, "rc_control": 10, "regeneration": 10, "quinque_aptitude": 10, "intellect": 10}
        
        final_attrs = base_attrs.copy()
        if self.creation_state.chosen_family_data and 'bonus' in self.creation_state.chosen_family_data:
            for attr, bonus_val in self.creation_state.chosen_family_data['bonus'].items():
                if attr in final_attrs:
                    final_attrs[attr] += bonus_val
        
        # Dados para a tabela 'characters'
        character_db_data = {
            'user_id': self.creation_state.author_id,
            'name': self.creation_state.character_name_ic, # Nome IC vai para o 'name' principal do personagem
            'faction': self.creation_state.faction,
            'level': 1, # Nível inicial
            'experience': 0, # XP inicial
            'strength': final_attrs['strength'],
            'agility': final_attrs['agility'],
            'resistance': final_attrs['resistance'],
            'health': final_attrs['health'], # Vida inicial pode ser baseada na resistência ou um valor fixo
            'max_health': final_attrs['max_health'],
            'stamina': final_attrs['stamina'],
            'max_stamina': final_attrs['max_stamina'],
            'kagune_quinque': self.creation_state.chosen_initial_ability_data['tipo'] if self.creation_state.chosen_initial_ability_data else "Básico",
            'created_at': discord.utils.utcnow().isoformat(),
            'ic_name': self.creation_state.character_name_ic,
            'age': self.creation_state.age,
            'gender': self.creation_state.gender,
            'appearance': self.creation_state.appearance,
            'backstory': self.creation_state.backstory,
            'perception': final_attrs['perception'],
            'rc_control': final_attrs['rc_control'] if self.creation_state.faction == 'ghoul' else base_attrs['rc_control'],
            'regeneration': final_attrs['regeneration'] if self.creation_state.faction == 'ghoul' else base_attrs['regeneration'],
            'quinque_aptitude': final_attrs['quinque_aptitude'] if self.creation_state.faction == 'ccg' else base_attrs['quinque_aptitude'],
            'intellect': final_attrs['intellect'] if self.creation_state.faction == 'ccg' else base_attrs['intellect'],
            # Adicione aqui a família e habilidade inicial se for salvar na tabela characters
            # 'familia': self.creation_state.chosen_family_data['nome'] if self.creation_state.chosen_family_data else None,
        }

        # Dados para a tabela 'players' (sistema de XP/Nível)
        player_db_data = {
            'user_id': self.creation_state.author_id,
            'level': 1,
            'xp': 0.0,
            'stat_points': 0, # Pode dar alguns pontos iniciais ou bônus da família
            'created_at': discord.utils.utcnow().isoformat()
        }
        if self.creation_state.chosen_family_data and 'bonus_stat_points' in self.creation_state.chosen_family_data['bonus']:
             player_db_data['stat_points'] += self.creation_state.chosen_family_data['bonus']['bonus_stat_points']


        success_char = await self.creation_state.bot.db.create_character(**character_db_data)
        # Certifique-se que create_player não falhe se o jogador já existir por causa do !xp
        # Ou crie um update_or_create_player
        player_exists = await self.creation_state.bot.db.get_player(self.creation_state.author_id)
        if player_exists:
            success_player = await self.creation_state.bot.db.update_player(self.creation_state.author_id, **player_db_data)
        else:
            success_player = await self.creation_state.bot.db.create_player(self.creation_state.author_id, **player_db_data)


        if success_char and success_player:
            await interaction.response.edit_message(content=f"✅ Personagem **{self.creation_state.character_name_ic}** criado com sucesso! Use `!perfil` para vê-lo.", embed=None, view=None)
        else:
            await interaction.response.edit_message(content="❌ Falha ao salvar o personagem no banco de dados. Tente novamente ou contate um admin.", embed=None, view=None)
        self.stop()

    @ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger, custom_id="cancel_creation_final")
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="Criação de personagem cancelada.", embed=None, view=None)
        self.stop()


# --- VIEW PARA ROLL DE FAMÍLIA ---
class FamilyRollView(ui.View):
    def __init__(self, creation_state: CreationState):
        super().__init__(timeout=300)
        self.creation_state = creation_state
        self.rolls_left = 3
        self.rolled_families_details = [] # Guarda {"nome": ..., "bonus": ..., "raridade": ..., "descricao": ...}

        # Adiciona botões de escolha dinamicamente depois dos rolls
        self.roll_button = ui.Button(label=f"🎲 Rolar Família ({self.rolls_left} restantes)", style=discord.ButtonStyle.success, custom_id="roll_family_btn")
        self.roll_button.callback = self.roll_family_callback
        self.add_item(self.roll_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.creation_state.author_id:
            await interaction.response.send_message("Estes botões não são para você!", ephemeral=True)
            return False
        return True

    def get_random_family(self):
        families_by_rarity = self.creation_state.get_family_list_for_faction()
        
        # Lógica de sorteio ponderada por raridade (exemplo simples)
        # Você pode implementar uma lógica mais sofisticada aqui
        # Ex: 60% Comum, 30% Rara, 10% Épica
        # Por agora, vamos pegar uma aleatória de qualquer raridade para simplificar
        all_families = []
        for rarity_group in families_by_rarity.values():
            all_families.extend(rarity_group)
        
        if not all_families:
            return {"nome": "Sem Família Definida", "bonus": {}, "raridade": "N/A", "descricao": "Configure as famílias no config.py"}
        
        return random.choice(all_families)

    async def roll_family_callback(self, interaction: discord.Interaction):
        if self.rolls_left > 0:
            self.rolls_left -= 1
            rolled_family = self.get_random_family()
            
            # Evitar duplicatas exatas na lista de opções, se possível (opcional)
            # if rolled_family not in self.rolled_families_details:
            self.rolled_families_details.append(rolled_family)

            self.roll_button.label = f"🎲 Rolar Família ({self.rolls_left} restantes)"
            if self.rolls_left == 0:
                self.roll_button.disabled = True
            
            embed = discord.Embed(title=f"📜 Escolha de Família ({self.creation_state.faction.capitalize()}) - Roll {3 - self.rolls_left}/3", color=0x7289da)
            description = "Você rolou as seguintes famílias:\n\n"
            for i, fam in enumerate(self.rolled_families_details):
                description += f"**Opção {i+1}: {fam['nome']}** ({fam['raridade']})\n"
                description += f"*Descrição:* {fam['descricao']}\n"
                description += f"*Bônus:* "
                bonus_str = ", ".join([f"{k.capitalize()}: +{v}" for k, v in fam['bonus'].items()])
                description += f"{bonus_str if bonus_str else 'Nenhum'}\n\n"
            
            if self.rolls_left > 0:
                description += "\nClique em 'Rolar Família' novamente ou, se já rolou o suficiente, aguarde o botão de escolha aparecer quando os rolls acabarem."
            else:
                description += "\nVocê usou todos os seus rolls. Agora escolha uma das famílias abaixo."

            embed.description = description
            
            # Atualizar botões de escolha SE os rolls acabaram
            if self.rolls_left == 0:
                self.clear_items() # Remove o botão de rolar
                for i, fam_data in enumerate(self.rolled_families_details):
                    choose_btn = ui.Button(label=f"Escolher {fam_data['nome']}", style=discord.ButtonStyle.primary, custom_id=f"choose_fam_{i}")
                    async def choose_callback(interaction, button_ref=choose_btn, chosen_fam=fam_data): # Captura chosen_fam
                        await self.select_family(interaction, chosen_fam)
                    choose_btn.callback = choose_callback
                    self.add_item(choose_btn)

            await interaction.response.edit_message(embed=embed, view=self)
        
        if self.rolls_left == 0 and not any(isinstance(item, ui.Button) and item.custom_id and item.custom_id.startswith("choose_fam_") for item in self.children):
             # Caso especial: se os rolls acabaram mas os botões de escolha não foram adicionados (ex: só 1 roll)
            self.clear_items()
            for i, fam_data in enumerate(self.rolled_families_details):
                choose_btn = ui.Button(label=f"Escolher {fam_data['nome']}", style=discord.ButtonStyle.primary, custom_id=f"choose_fam_{i}")
                async def choose_callback(interaction, button_ref=choose_btn, chosen_fam=fam_data):
                    await self.select_family(interaction, chosen_fam)
                choose_btn.callback = choose_callback
                self.add_item(choose_btn)
            await interaction.message.edit(view=self) # Re-edita para mostrar os botões de escolha

    async def select_family(self, interaction: discord.Interaction, family_data):
        self.creation_state.chosen_family_data = family_data
        
        for item in self.children: # Desabilita botões de escolha de família
            item.disabled = True
        await interaction.response.edit_message(view=self) # Atualiza a view para desabilitar

        # Próximo passo: Roll de Habilidade/Arma
        ability_view = InitialAbilityWeaponRollView(self.creation_state)
        embed = discord.Embed(title=f"✨ Escolha de Habilidade/Arma Inicial ({self.creation_state.faction.capitalize()})", description="Clique no botão para rolar sua habilidade ou arma inicial (até 2 vezes).", color=0x9b59b6)
        if self.creation_state.message_to_edit:
            await self.creation_state.message_to_edit.edit(embed=embed, view=ability_view)
        else: # Fallback
            self.creation_state.message_to_edit = await interaction.followup.send(embed=embed, view=ability_view, ephemeral=False)


# --- VIEW PARA ROLL DE HABILIDADE/ARMA INICIAL ---
class InitialAbilityWeaponRollView(ui.View):
    def __init__(self, creation_state: CreationState):
        super().__init__(timeout=300)
        self.creation_state = creation_state
        self.rolls_left = 2 # Exemplo: 2 rolls para habilidade/arma
        self.rolled_options_details = []

        self.roll_button = ui.Button(label=f"🎲 Rolar Habilidade/Arma ({self.rolls_left} restantes)", style=discord.ButtonStyle.success, custom_id="roll_ability_btn")
        self.roll_button.callback = self.roll_ability_callback
        self.add_item(self.roll_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.creation_state.author_id:
            await interaction.response.send_message("Estes botões não são para você!", ephemeral=True)
            return False
        return True

    def get_random_initial_ability_weapon(self):
        options = self.creation_state.get_initial_ability_list_for_faction()
        if not options:
            return {"nome": "Básico", "tipo": "Padrão", "descricao": "Habilidade/Arma inicial padrão."}
        return random.choice(options)

    async def roll_ability_callback(self, interaction: discord.Interaction):
        if self.rolls_left > 0:
            self.rolls_left -= 1
            rolled_option = self.get_random_initial_ability_weapon()
            self.rolled_options_details.append(rolled_option)

            self.roll_button.label = f"🎲 Rolar Habilidade/Arma ({self.rolls_left} restantes)"
            if self.rolls_left == 0:
                self.roll_button.disabled = True
            
            embed = discord.Embed(title=f"✨ Escolha de Habilidade/Arma ({self.creation_state.faction.capitalize()}) - Roll {2 - self.rolls_left}/2", color=0x9b59b6)
            description = "Você rolou as seguintes opções:\n\n"
            for i, opt in enumerate(self.rolled_options_details):
                description += f"**Opção {i+1}: {opt['nome']}** (Tipo: {opt['tipo']})\n"
                description += f"*Descrição:* {opt['descricao']}\n\n"
            
            if self.rolls_left > 0:
                description += "\nClique em 'Rolar Habilidade/Arma' novamente ou aguarde o botão de escolha."
            else:
                description += "\nVocê usou todos os seus rolls. Agora escolha uma das opções abaixo."
            embed.description = description
            
            if self.rolls_left == 0:
                self.clear_items()
                for i, opt_data in enumerate(self.rolled_options_details):
                    choose_btn = ui.Button(label=f"Escolher {opt_data['nome']}", style=discord.ButtonStyle.primary, custom_id=f"choose_abil_{i}")
                    async def choose_callback(interaction, button_ref=choose_btn, chosen_opt=opt_data):
                        await self.select_initial_ability_weapon(interaction, chosen_opt)
                    choose_btn.callback = choose_callback
                    self.add_item(choose_btn)
            
            await interaction.response.edit_message(embed=embed, view=self)

        if self.rolls_left == 0 and not any(isinstance(item, ui.Button) and item.custom_id and item.custom_id.startswith("choose_abil_") for item in self.children):
            self.clear_items()
            for i, opt_data in enumerate(self.rolled_options_details):
                choose_btn = ui.Button(label=f"Escolher {opt_data['nome']}", style=discord.ButtonStyle.primary, custom_id=f"choose_abil_{i}")
                async def choose_callback(interaction, button_ref=choose_btn, chosen_opt=opt_data):
                    await self.select_initial_ability_weapon(interaction, chosen_opt)
                choose_btn.callback = choose_callback
                self.add_item(choose_btn)
            await interaction.message.edit(view=self)

    async def select_initial_ability_weapon(self, interaction: discord.Interaction, ability_data):
        self.creation_state.chosen_initial_ability_data = ability_data
        
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        # Próximo passo: Modal de Informações Pessoais
        info_modal = CharacterInfoModal(self.creation_state)
        # O modal é enviado, e o on_submit do modal chamará a ConfirmationView
        await interaction.followup.send_modal(info_modal) # Usar followup se a interação já foi respondida/deferida


# --- VIEW INICIAL PARA ESCOLHA DE FACÇÃO ---
class FactionChoiceView(ui.View):
    def __init__(self, creation_state: CreationState):
        super().__init__(timeout=180)
        self.creation_state = creation_state

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.creation_state.author_id:
            await interaction.response.send_message("Estes botões não são para você!", ephemeral=True)
            return False
        return True

    async def start_next_step(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        
        family_view = FamilyRollView(self.creation_state)
        embed = discord.Embed(title=f"📜 Escolha de Família ({self.creation_state.faction.capitalize()})", description="Clique no botão para rolar sua família (até 3 vezes).", color=0x7289da)
        
        if self.creation_state.message_to_edit:
            await self.creation_state.message_to_edit.edit(embed=embed, view=family_view)
        else: # Fallback
            self.creation_state.message_to_edit = await interaction.followup.send(embed=embed, view=family_view, ephemeral=False)


    @ui.button(label="👹 Ghoul", style=discord.ButtonStyle.danger, custom_id="criar_choose_ghoul")
    async def ghoul_button(self, interaction: discord.Interaction, button: ui.Button):
        self.creation_state.faction = "ghoul"
        await interaction.response.defer() 
        await self.start_next_step(interaction)

    @ui.button(label="🛡️ CCG", style=discord.ButtonStyle.primary, custom_id="criar_choose_ccg")
    async def ccg_button(self, interaction: discord.Interaction, button: ui.Button):
        self.creation_state.faction = "ccg"
        await interaction.response.defer()
        await self.start_next_step(interaction)