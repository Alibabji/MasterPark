"""
import discord
from discord.ui import modal, inputtext, select, view
import sqlite3

#데이터베이스에 연결, 없을시 생성.
conn=sqlite3.connect("user-info.db")
cursor = conn.cursor()

cursor.execute('''
    create table if not exists users (
        userid integer primary key,
        riotid text,
        tag text
    )
''')
conn.commit()

def save_user_data(userid, riotid,tag):
    cursor.execute('''
        insert into users (userid, riotid, tag)
        values (?, ?, ?)
        on conflict(userid) do update set riotid=excluded.riotid, tag=excluded.tag
    ''',(userid,riotid,tag))
    conn.commit()

# modal to get riot id
class getid(modal):
    def __init__(self):
        super().__init__(title="my modal")
        self.add_item(inputtext(label="닉네임:", placeholder="라이엇 닉네임을 입력해주세요"))
        self.add_item(inputtext(label="# 태그:", placeholder="라이엇 게임태그를 입력해주세요"))

    async def callback(self, interaction: discord.interaction):
        id = self.children[0].value
        tag = self.children[1].value
        save_user_data(interaction.user.id,id,tag)
        await interaction.response.send_message(f"라이엇 id: {id}#{tag} 저장되었습니다.", ephemeral=true)

# select menu for account sync option
class syncoption(select):
    def __init__(self):
        options = [
            discord.selectoption(label="계정연동", description="새로운 라이엇 계정을 연동합니다", value="0"),
            discord.selectoption(label="연동취소", description="연동된 계정을 해제합니다", value="1")
        ]
        super().__init__(placeholder="아래 옵션중 선택", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.interaction):
        if self.values[0] == "0":
            riot = getid()
            await interaction.response.send_modal(riot)
"""