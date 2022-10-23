import nextcord
import os
import json
from nextcord.ext import commands
from sqlalchemy import create_engine

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

config = json.loads(open("config.json", "r").read())
TEST_SERVER = config['TEST_SERVER_GUILD_ID']
TOKEN = config['TOKEN']
ENGINE_URL = config['ENGINE_URL']
del config['TOKEN']


class AttendanceBot(commands.Bot):
    test_server = TEST_SERVER
    engine = create_engine("sqlite:///database.db" if ENGINE_URL == "" else ENGINE_URL, echo=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def prefixes(cls, client: None, message):
        return "!"

    async def on_ready(self):
        print(f'{self.user} has connected to discord!')


if __name__ == "__main__":
    bot = AttendanceBot(command_prefix=AttendanceBot.prefixes, max_messages=20_000)
    from models import Module, Code, Lecture, Seminar, Base
    Base.metadata.create_all(AttendanceBot.engine)
    bot.load_extension('cogs.maincog')
    print("Trying to login...")
    bot.run(TOKEN)
    bot.sync_all_application_commands()
