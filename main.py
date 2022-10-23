import nextcord
import os
import json
from nextcord.ext import commands
from tools.database import connect

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

config = json.loads(open("config.json", "r").read())
TEST_SERVER = config['TEST_SERVER_GUILD_ID']
TOKEN = config['TOKEN']
del config['TOKEN']


class AttendanceBot(commands.Bot):
    connection, cursor = connect()
    test_server = TEST_SERVER

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def prefixes(cls, client: None, message):
        return "!"

    async def on_ready(self):
        print(f'{self.user} has connected to discord!')


if __name__ == "__main__":
    bot = AttendanceBot(command_prefix=AttendanceBot.prefixes, max_messages=20_000)
    bot.load_extension('cogs.maincog')
    print("Trying to login...")
    bot.run(TOKEN)
    bot.sync_all_application_commands()
