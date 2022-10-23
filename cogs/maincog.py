from main import AttendanceBot
import nextcord
from nextcord.ext import commands
from tools.database import get_attendance_codes, add_course, list_modules, remove_module, add_attendance_code, sqlite3, DoesNotExist, remove_attendance_code


class MainCog(commands.Cog):
    codes = []

    def __init__(self, bot: AttendanceBot):
        self.bot = bot
        # Inherit the connection from the Client defined in main.py
        self.connection, self.c = self.bot.connection, self.bot.cursor

    @nextcord.slash_command(name="ping", guild_ids=[AttendanceBot.test_server])
    async def ping(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("Pong!")

    @nextcord.slash_command(name="sourcecode")
    async def sourcecode(self, interaction: nextcord.Interaction):
        """Sends the source code of the bot

        Parameters
        ----------
        interaction : nextcord.Interaction
            The interaction object
        :return:
        """
        await interaction.response.send_message("https://github.com/Scot-Survivor/AttendanceCodeBot")

    @nextcord.slash_command(name="codes")
    async def codes(self, interaction: nextcord.Interaction):
        """
        Lists all attendance codes

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        :return:
        """
        self.codes = get_attendance_codes(self.c)
        embed = nextcord.Embed(title="Attendance Codes", description="List of all attendance codes", color=0x00ff00)
        for code in self.codes:
            embed.add_field(name=code[0], value=code[1], inline=False)
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="addcode")
    async def addcode(self, interaction: nextcord.Interaction, code: str, course: str):
        """
        Adds a new attendance code

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        code: str
            The code to add
        module: str
            The module the code is for
        :return:
        """
        try:
            add_attendance_code(self.c, course.strip(), code.strip())
            self.connection.commit()
        except sqlite3.IntegrityError:
            await interaction.response.send_message("That code already exists!")
        except DoesNotExist:
            await interaction.response.send_message("That module does not exist!")
        else:
            await interaction.response.send_message(f"Added code! {code} for {course}")

    @nextcord.slash_command(name="addmodule", default_member_permissions=nextcord.Permissions(administrator=True))
    async def addmodule(self, interaction: nextcord.Interaction, module: str,
                        module_code: str):
        """
        Adds a new module: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        module: str
            The module to add
        module_code: str
            The module code, I.E COMP38200
        :return:
        """
        add_course(self.c, module, module_code)
        self.connection.commit()
        await interaction.response.send_message(f"Added module: {module}!")

    @nextcord.slash_command(name="modules")
    async def modules(self, interaction: nextcord.Interaction):
        """
        Lists all courses

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        :return:
        """
        modules = list_modules(self.c)
        embed = nextcord.Embed(title="Courses", description="List of all courses", color=0x00ff00)
        for module in modules:
            embed.add_field(name=module[0], value=module[1], inline=False)
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="removemodule", default_member_permissions=nextcord.Permissions(administrator=True))
    async def removemodule(self, interaction: nextcord.Interaction, module: str):
        """
        Removes a module: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        module: str
            The module to remove
        :return:
        """
        remove_module(self.c, module)
        self.connection.commit()
        await interaction.response.send_message(f"Removed module: {module}!")

    @nextcord.slash_command(name="removecode", default_member_permissions=nextcord.Permissions(administrator=True))
    async def removecode(self, interaction: nextcord.Interaction, code: str):
        """
        Removes an attendance code: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        code: str
            The code to remove
        :return:
        """
        remove_attendance_code(self.c, code)
        self.connection.commit()
        await interaction.response.send_message(f"Removed code: {code}!")

    @nextcord.slash_command(name="help")
    async def help(self, interaction: nextcord.Interaction):
        """
        Shows the help command

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        :return:
        """
        embed = nextcord.Embed(title="Help", description="List of all commands", color=0x00ff00)
        embed.add_field(name="/codes", value="Lists all attendance codes", inline=False)
        embed.add_field(name="/addcode", value="Adds a new attendance code", inline=False)
        embed.add_field(name="/addmodule", value="Adds a new module", inline=False)
        embed.add_field(name="/modules", value="Lists all courses", inline=False)
        embed.add_field(name="/removemodule", value="Removes a module", inline=False)
        embed.add_field(name="/removecode", value="Removes an attendance code", inline=False)
        embed.add_field(name="/sourcecode", value="Sends the source code of the bot", inline=False)
        embed.add_field(name="/help", value="Shows the help command", inline=False)
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(MainCog(bot))
