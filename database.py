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
                    kagune_quinque TEXT,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_combat TEXT,
                    status TEXT DEFAULT 'ativo'
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
