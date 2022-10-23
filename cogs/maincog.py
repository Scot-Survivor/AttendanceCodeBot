import nextcord
import datetime
from main import AttendanceBot
from nextcord.ext import commands
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.Code import Code
from models.Module import Module
from models.Seminar import Seminar
from models.Lecture import Lecture


class MainCog(commands.Cog):
    codes = []

    def __init__(self, bot: AttendanceBot):
        self.bot = bot
        self.engine = bot.engine


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
        NOW = datetime.datetime.utcnow()
        HOUR_FORWARD = NOW + datetime.timedelta(hours=1)
        HOUR_24_AGO = NOW - datetime.timedelta(hours=24)
        stmt = select(Code).filter(Code.created_at.between(HOUR_24_AGO, HOUR_FORWARD))
        session = Session(self.engine)
        codes = session.execute(stmt).scalars().all()
        embed = nextcord.Embed(title="Attendance Codes", description="List of all attendance codes", color=0x00ff00)
        for code in codes:
            embed.add_field(name=code[0], value=code[1], inline=False)
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="addcode")
    async def addcode(self, interaction: nextcord.Interaction, code: str, module_code: str,
                      seminar_name: str = None, lecture_name: str = None):
        """
        Adds a new attendance code

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        code: str
            The code to add
        module_code: str
            The module the code is for
        seminar_name: str
            The seminar the code is for, if applicable
            "Introduction to Programming Group 14"
        lecture_name: str
            The lecture the code is for, if applicable
            "Introduction to OOP Lecture 1"
        :return:
        """
        if seminar_name is None and lecture_name is None:
            await interaction.response.send_message("You must specify at either a seminar or lecture name")
            return

        stmt = select(Module).where(Module.module_code == module_code)
        session = Session(self.engine)
        module = session.execute(stmt).scalars().first()

        if module is None:
            await interaction.response.send_message("Module does not exist")
            return

        with Session(self.engine) as session:
            stmt = select(Seminar).where(Seminar.name == seminar_name)
            obj_seminar = session.execute(stmt).scalars().first()
            stmt = select(Lecture).where(Lecture.name == lecture_name)
            obj_lecture = session.execute(stmt).scalars().first()
            if (seminar_name is not None and obj_seminar is None) or (lecture_name is not None and obj_lecture is None):
                await interaction.response.send_message("Seminar or lecture does not exist. Please ask an admin to create it")
                return

            if obj_seminar is not None:
                obj_code = Code(code=code, module_id=module.id, seminar_id=obj_seminar.id)
            elif obj_lecture is not None:
                obj_code = Code(code=code, module_id=module.id, lecture_id=obj_lecture.id)

            session.add(obj_code)
            session.commit()

        await interaction.response.send_message(f"Added code! {code} for {module.name}")

    @nextcord.slash_command(name="seminars")
    async def seminars(self, interaction: nextcord.Interaction, module_code: str):
        """
        Lists all seminars for a module

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        module_code: str
            The module code to list seminars for
        :return:
        """
        stmt = select(Module).where(Module.module_code == module_code)
        session = Session(self.engine)
        module = session.execute(stmt).scalars().first()

        if module is None:
            await interaction.response.send_message("Module does not exist")
            return

        stmt = select(Seminar).where(Seminar.module_id == module.id)
        seminars = session.execute(stmt).scalars().all()
        embed = nextcord.Embed(title="Seminars", description=f"List of all seminars for {module.name}", color=0x00ff00)
        for seminar in seminars:
            embed.add_field(name=seminar.name, value=seminar.id, inline=False)
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="lectures")
    async def lectures(self, interaction: nextcord.Interaction, module_code: str):
        """
        Lists all lectures for a module

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        module_code: str
            The module code to list lectures for
        :return:
        """
        stmt = select(Module).where(Module.module_code == module_code)
        session = Session(self.engine)
        module = session.execute(stmt).scalars().first()

        if module is None:
            await interaction.response.send_message("Module does not exist")
            return

        stmt = select(Lecture).where(Lecture.module_id == module.id)
        lectures = session.execute(stmt).scalars().all()
        embed = nextcord.Embed(title="Lectures", description=f"List of all lectures for {module.name}", color=0x00ff00)
        for lecture in lectures:
            embed.add_field(name=lecture.name, value=lecture.id, inline=False)
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="addmodule", default_member_permissions=nextcord.Permissions(administrator=True))
    async def addmodule(self, interaction: nextcord.Interaction, name: str, module_code: str, description: str = ""):
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
        with Session(self.engine) as session:
            obj_module = Module(name=name, module_code=module_code, description=description)
            session.add(obj_module)
            session.commit()
        await interaction.response.send_message(f"Added module! {name}")

    @nextcord.slash_command(name="addseminar", default_member_permissions=nextcord.Permissions(administrator=True))
    async def addseminar(self, interaction: nextcord.Interaction, name: str, module_code: str):
        """
        Adds a new seminar: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        name: str
            The name of the seminar
        module_code: str
            The module code, I.E COMP38200
        :return:
        """
        stmt = select(Module).where(Module.module_code == module_code)
        session = Session(self.engine)
        module = session.execute(stmt).scalars().first()

        if module is None:
            await interaction.response.send_message("Module does not exist")
            return

        with Session(self.engine) as session:
            obj_seminar = Seminar(name=name, module_id=module.id)
            session.add(obj_seminar)
            session.commit()
        await interaction.response.send_message(f"Added seminar! {name}")

    @nextcord.slash_command(name="addlecture", default_member_permissions=nextcord.Permissions(administrator=True))
    async def addlecture(self, interaction: nextcord.Interaction, name: str, module_code: str):
        """
        Adds a new lecture: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        name: str
            The name of the lecture
        module_code: str
            The module code, I.E COMP38200
        :return:
        """
        stmt = select(Module).where(Module.module_code == module_code)
        session = Session(self.engine)
        module = session.execute(stmt).scalars().first()

        if module is None:
            await interaction.response.send_message("Module does not exist")
            return

        with Session(self.engine) as session:
            obj_lecture = Lecture(name=name, module_id=module.id)
            session.add(obj_lecture)
            session.commit()
        await interaction.response.send_message(f"Added lecture! {name}")

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
        stmt = select(Module)
        session = Session(self.engine)
        modules = session.execute(stmt).scalars().all()
        embed = nextcord.Embed(title="Modules", description="List of all modules", color=0x00ff00)
        for module in modules:
            embed.add_field(name=module.name + " : " + module.module_code, value="N/A" if module.description == "" else module.description, inline=False)
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="removemodule", default_member_permissions=nextcord.Permissions(administrator=True))
    async def removemodule(self, interaction: nextcord.Interaction, module_code: str):
        """
        Removes a module: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        module_code: str
            The module (by code) to remove
        :return:
        """
        with Session(self.engine) as session:
            stmt = select(Module).where(Module.module_code == module_code)
            module = session.execute(stmt).scalars().first()
            session.delete(module)
            session.commit()
        await interaction.response.send_message(f"Removed module! {module_code}")

    @nextcord.slash_command(name="removecode", default_member_permissions=nextcord.Permissions(administrator=True))
    async def removecode(self, interaction: nextcord.Interaction, code: str, module_code: str):
        """
        Removes a code: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        code: str
            The code to remove
        module: str
            The module the code is for
        :return:
        """
        with Session(self.engine) as session:
            stmt = select(Module).where(Module.module_code == module_code)
            module = session.execute(stmt).scalars().first()
            stmt = select(Code).where(Code.code == code)
            code = session.execute(stmt).scalars().first()
            session.delete(code)
            session.commit()
        await interaction.response.send_message(f"Removed code! {code} for {module.name}")

    @nextcord.slash_command(name="removelecture", default_member_permissions=nextcord.Permissions(administrator=True))
    async def removelecture(self, interaction: nextcord.Interaction, lecture_name: str):
        """
        Removes a lecture: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        lecture_name: str
            The name of the lecture to remove
        :return:
        """
        with Session(self.engine) as session:
            stmt = select(Lecture).where(Lecture.name == lecture_name)
            lecture = session.execute(stmt).scalars().first()
            session.delete(lecture)
            session.commit()
        await interaction.response.send_message(f"Removed lecture! {lecture_name}")

    @nextcord.slash_command(name="removeseminar", default_member_permissions=nextcord.Permissions(administrator=True))
    async def removeseminar(self, interaction: nextcord.Interaction, seminar_name: str):
        """
        Removes a seminar: Admin only

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        seminar_name: str
            The name of the seminar to remove
        :return:
        """
        with Session(self.engine) as session:
            stmt = select(Seminar).where(Seminar.name == seminar_name)
            seminar = session.execute(stmt).scalars().first()
            session.delete(seminar)
            session.commit()
        await interaction.response.send_message(f"Removed seminar! {seminar_name}")

    @nextcord.slash_command(name="help", description="Shows this message")
    async def help(self, interaction: nextcord.Interaction):
        """
        Shows the help message

        Parameters
        __________
        interaction: nextcord.Interaction
            The interaction object
        :return:
        """
        embed = nextcord.Embed(title="Help", description="List of all commands", color=0x00ff00)
        for command in self.bot.get_application_commands(rollout=False):
            embed.add_field(name=command.name, value=command.description, inline=False)
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(MainCog(bot))
