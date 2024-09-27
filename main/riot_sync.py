import discord
from discord.ui import Modal, InputText, Select, View
import sqlite3

#데이터베이스에 연결, 없을시 생성.
conn=sqlite3.connect("user-info.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        userID INTEGER PRIMARY KEY,
        riotID TEXT,
        tag TEXT
    )
''')
conn.commit()

def save_user_data(userID, riotID,tag):
    cursor.execute('''
        INSERT INTO users (userID, riotID, tag)
        VALUES (?, ?, ?)
        ON CONFLICT(userID) DO UPDATE SET riotID=excluded.riotID, tag=excluded.tag
    ''',(userID,riotID,tag))
    conn.commit()

# Modal to get Riot ID
class getID(Modal):
    def __init__(self):
        super().__init__(title="My Modal")
        self.add_item(InputText(label="닉네임:", placeholder="라이엇 닉네임을 입력해주세요"))
        self.add_item(InputText(label="# 태그:", placeholder="라이엇 게임태그를 입력해주세요"))

    async def callback(self, interaction: discord.Interaction):
        ID = self.children[0].value
        tag = self.children[1].value
        save_user_data(interaction.user.id,ID,tag)
        await interaction.response.send_message(f"라이엇 ID: {ID}#{tag} 저장되었습니다.", ephemeral=True)

# Select menu for account sync option
class syncOption(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="계정연동", description="새로운 라이엇 계정을 연동합니다", value="0"),
            discord.SelectOption(label="연동취소", description="연동된 계정을 해제합니다", value="1")
        ]
        super().__init__(placeholder="아래 옵션중 선택", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "0":
            riot = getID()
            await interaction.response.send_modal(riot)


