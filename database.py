import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self, db_path="tokyo_ghoul.db"):
        self.db_path = db_path
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """Inicializa o banco de dados e cria as tabelas necessárias"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de personagens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    faction TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    strength INTEGER DEFAULT 10,
                    agility INTEGER DEFAULT 10,
                    resistance INTEGER DEFAULT 10,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    stamina INTEGER DEFAULT 50,
                    max_stamina INTEGER DEFAULT 50,
                    kagune_quinque TEXT,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_combat TEXT,
                    status TEXT DEFAULT 'ativo',
                    ic_name TEXT DEFAULT '',
                    age TEXT DEFAULT '',
                    gender TEXT DEFAULT '',
                    appearance TEXT DEFAULT '',
                    backstory TEXT DEFAULT '',
                    perception INTEGER DEFAULT 10,
                    rc_control INTEGER DEFAULT 10,
                    regeneration INTEGER DEFAULT 10,
                    quinque_aptitude INTEGER DEFAULT 10,
                    intellect INTEGER DEFAULT 10
                )
            """)
            
            # Tabela de combates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS combat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attacker_id INTEGER NOT NULL,
                    defender_id INTEGER NOT NULL,
                    winner_id INTEGER,
                    combat_data TEXT,
                    experience_gained INTEGER,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (attacker_id) REFERENCES characters (user_id),
                    FOREIGN KEY (defender_id) REFERENCES characters (user_id)
                )
            """)
            
            # Tabela de cooldowns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id INTEGER,
                    command_type TEXT,
                    expires_at TEXT,
                    PRIMARY KEY (user_id, command_type)
                )
            """)
            
            # Tabela de jogadores (sistema XP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    level INTEGER DEFAULT 1,
                    xp REAL DEFAULT 0.0,
                    stat_points INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Tabela de canais XP
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS xp_channels (
                    channel_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    added_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            logging.info("Banco de dados inicializado com sucesso!")
    
    async def create_character(self, user_id, name, faction, kagune_quinque):
        """Cria um novo personagem"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO characters 
                    (user_id, name, faction, kagune_quinque, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, name, faction, kagune_quinque,
 datetime.now().isoformat()))
                
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()
    
    async def get_character(self, user_id):
        """Obtém dados do personagem"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
    
    async def update_character(self, user_id, **kwargs):
        """Atualiza dados do personagem"""
        async with self.lock:
            if not kwargs:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construir query dinamicamente
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            
            cursor.execute(f"UPDATE characters SET {set_clause} WHERE user_id = ?", values)
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
    
    async def add_experience(self, user_id, exp_gain):
        """Adiciona experiência e verifica se subiu de nível"""
        character = await self.get_character(user_id)
        if not character:
            return False, 0
        
        new_exp = character['experience'] + exp_gain
        old_level = character['level']
        new_level = self._calculate_level(new_exp)
        
        update_data = {'experience': new_exp}
        
        # Se subiu de nível, aumentar atributos
        if new_level > old_level:
            levels_gained = new_level - old_level
            update_data.update({
                'level': new_level,
                'strength': character['strength'] + levels_gained * 2,
                'agility': character['agility'] + levels_gained * 2,
                'resistance': character['resistance'] + levels_gained * 2,
                'max_health': character['max_health'] + levels_gained * 10
            })
            # Curar completamente ao subir de nível
            update_data['health'] = update_data['max_health']
        
        await self.update_character(user_id, **update_data)
        levels_gained = new_level - old_level if new_level > old_level else 0
        return new_level > old_level, levels_gained
    
    def _calculate_level(self, experience):
        """Calcula o nível baseado na experiência"""
        # Fórmula: nível = sqrt(exp / 100) + 1
        import math
        return min(50, int(math.sqrt(experience / 100)) + 1)  # Nível máximo 50
    
    def _experience_for_level(self, level):
        """Calcula experiência necessária para um nível"""
        return (level - 1) ** 2 * 100
    
    async def log_combat(self, attacker_id, defender_id, winner_id, combat_data, exp_gained):
        """Registra um combate no log"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO combat_logs 
                (attacker_id, defender_id, winner_id, combat_data, experience_gained, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (attacker_id, defender_id, winner_id, 
                  json.dumps(combat_data), exp_gained, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
    
    async def set_cooldown(self, user_id, command_type, duration_minutes):
        """Define um cooldown para um usuário"""
        async with self.lock:
            expires_at = datetime.now() + timedelta(minutes=duration_minutes)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO cooldowns (user_id, command_type, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, command_type, expires_at.isoformat()))
            
            conn.commit()
            conn.close()
    
    async def check_cooldown(self, user_id, command_type):
        """Verifica se um usuário está em cooldown"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT expires_at FROM cooldowns 
                WHERE user_id = ? AND command_type = ?
            """, (user_id, command_type))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                expires_at = datetime.fromisoformat(result[0])
                if datetime.now() < expires_at:
                    remaining = expires_at - datetime.now()
                    return True, remaining.total_seconds()
                else:
                    # Cooldown expirado, remover
                    await self._remove_cooldown(user_id, command_type)
            
            return False, 0
    
    async def _remove_cooldown(self, user_id, command_type):
        """Remove um cooldown expirado"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM cooldowns 
                WHERE user_id = ? AND command_type = ?
            """, (user_id, command_type))
            
            conn.commit()
            conn.close()
    
    async def get_leaderboard(self, criteria='level', limit=10):
        """Obtém ranking de jogadores"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            valid_criteria = ['level', 'wins', 'experience']
            if criteria not in valid_criteria:
                criteria = 'level'
            
            cursor.execute(f"""
                SELECT user_id, name, faction, level, wins, losses, experience
                FROM characters 
                WHERE status = 'ativo'
                ORDER BY {criteria} DESC, experience DESC
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
    
    async def create_player(self, user_id):
        """Cria um novo jogador no sistema XP"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO players (user_id, created_at)
                    VALUES (?, ?)
                """, (user_id, datetime.now().isoformat()))
                
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()
    
    async def get_player(self, user_id):
        """Obtém dados do jogador"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
    
    async def add_xp(self, user_id, xp_amount):
        """Adiciona XP ao jogador e verifica level up"""
        player = await self.get_player(user_id)
        if not player:
            # Criar jogador se não existir
            await self.create_player(user_id)
            player = await self.get_player(user_id)
        
        if not player:
            return False, 1, 1, 0
        
        old_level = player['level']
        new_xp = player['xp'] + xp_amount
        new_level = self._calculate_level_from_xp(new_xp)
        
        update_data = {'xp': new_xp}
        stat_points_gained = 0
        
        # Se subiu de nível
        if new_level > old_level:
            levels_gained = new_level - old_level
            stat_points_gained = levels_gained * 3  # 3 pontos por nível
            update_data.update({
                'level': new_level,
                'stat_points': player['stat_points'] + stat_points_gained
            })
        
        await self.update_player(user_id, **update_data)
        return new_level > old_level, old_level, new_level, stat_points_gained
    
    async def update_player(self, user_id, **kwargs):
        """Atualiza dados do jogador"""
        async with self.lock:
            if not kwargs:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            
            cursor.execute(f"UPDATE players SET {set_clause} WHERE user_id = ?", values)
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
    
    def _calculate_level_from_xp(self, xp):
        """Calcula o nível baseado no XP total"""
        if xp < 100:
            return 1
        
        level = 1
        xp_needed = 100  # XP base para nível 2
        total_xp_used = 0
        
        while total_xp_used + xp_needed <= xp:
            total_xp_used += xp_needed
            level += 1
            xp_needed = int(xp_needed * 1.2)  # Aumenta 20%
        
        return level
    
    def _xp_needed_for_level(self, target_level):
        """Calcula XP total necessário para alcançar um nível"""
        if target_level <= 1:
            return 0
        
        total_xp = 0
        xp_needed = 100  # XP base para nível 2
        
        for level in range(2, target_level + 1):
            total_xp += xp_needed
            xp_needed = int(xp_needed * 1.2)
        
        return total_xp
    
    def _xp_for_next_level(self, current_level):
        """Calcula XP necessário para o próximo nível"""
        if current_level == 1:
            return 100
        
        xp_needed = 100
        for i in range(2, current_level + 1):
            xp_needed = int(xp_needed * 1.2)
        
        return xp_needed
    
    async def add_xp_channel(self, channel_id, guild_id):
        """Adiciona canal à lista de canais XP"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO xp_channels (channel_id, guild_id, added_at)
                    VALUES (?, ?, ?)
                """, (channel_id, guild_id, datetime.now().isoformat()))
                
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()
    
    async def remove_xp_channel(self, channel_id):
        """Remove canal da lista de canais XP"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM xp_channels WHERE channel_id = ?", (channel_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
    
    async def is_xp_channel(self, channel_id):
        """Verifica se o canal está na lista de canais XP"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM xp_channels WHERE channel_id = ?", (channel_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
    
    async def get_xp_channels(self, guild_id):
        """Obtém todos os canais XP de um servidor"""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT channel_id FROM xp_channels WHERE guild_id = ?", (guild_id,))
            results = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in results]