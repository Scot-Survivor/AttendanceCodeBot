import asyncio
import datetime
import typing

import nextcord
from nextcord.ext import commands
from sqlalchemy import select
from sqlalchemy.orm import Session

from main import AttendanceBot
from models.Code import Code
from models.Lecture import Lecture
from models.Module import Module
from models.Seminar import Seminar
from ui_components.AddCode import AddCodeView


class MainCog(commands.Cog):
    codes = []

    def __init__(self, bot: AttendanceBot):
        self.bot = bot
        self.engine = bot.engine
        self.bot.loop.create_task(self.clear_codes_older_than_a_day())
        self.bot.loop.create_task(self.clear_duplicate_codes())

    async def get_module(self, module_code: str, interaction: nextcord.Interaction) -> typing.Union[Module, None]:
        stmt = select(Module).where(Module.module_code == module_code)
        session = Session(self.engine)
        module = session.execute(stmt).scalars().first()

        if module is None:
            await interaction.response.send_message("Module does not exist")
            return
        return module

    async def clear_codes_older_than_a_day(self):
        with Session(self.engine) as session:
            stmt = select(Code).where(Code.created_at < datetime.datetime.now() - datetime.timedelta(days=1))
            codes = session.execute(stmt).scalars().all()
            for code in codes:
                session.delete(code)
            session.commit()

        await asyncio.sleep(60 * 60 * 24)

    async def clear_duplicate_codes(self):
        with Session(self.engine) as session:
            codes = session.execute(select(Code)).scalars().all()
            for code in codes:
                stmt = select(Code).where(Code.code == code.code)
                codes = session.execute(stmt).scalars().all()
                if len(codes) > 1:
                    for i_code in codes[1:]:
                        session.delete(i_code)
            session.commit()

        await asyncio.sleep(60 * 60 * 24)

    async def get_number_of_modules(self):
        with Session(self.engine) as session:
            return len(session.execute(select(Module)).all())

    async def get_number_of_codes(self):
        with Session(self.engine) as session:
            return len(session.execute(select(Code)).all())

    async def get_number_of_seminars(self):
        with Session(self.engine) as session:
            return len(session.execute(select(Seminar)).all())

    async def get_number_of_lectures(self):
        with Session(self.engine) as session:
            return len(session.execute(select(Lecture)).all())

    @nextcord.slash_command(name="ping", guild_ids=[AttendanceBot.test_server])
    async def ping(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("Pong!")

    @nextcord.slash_command("stats")
    async def stats(self, interaction: nextcord.Interaction):
        """
        Shows the stats of the bot
        """
        number_of_modules = await self.get_number_of_modules()
        number_of_lectures = await self.get_number_of_lectures()
        number_of_seminars = await self.get_number_of_seminars()
        number_of_codes = await self.get_number_of_codes()
        embed = nextcord.Embed(title="Stats", description="Shows the stats of the bot", color=nextcord.Color.green())
        embed.add_field(name="Number of modules", value=number_of_modules, inline=False)
        embed.add_field(name="Number of lectures", value=number_of_lectures, inline=False)
        embed.add_field(name="Number of seminars", value=number_of_seminars, inline=False)
        embed.add_field(name="Number of codes", value=number_of_codes, inline=False)
        embed.set_footer(text=f"Requested by {interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

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
        now = datetime.datetime.utcnow()
        hour_forward = now + datetime.timedelta(hours=1)
        hour_2_ago = now - datetime.timedelta(hours=2)
        stmt = select(Code).filter(Code.created_at.between(hour_2_ago, hour_forward))
        session = Session(self.engine)
        codes = session.execute(stmt).scalars().all()
        embed = nextcord.Embed(title="Attendance Codes", description="List of all attendance codes", color=0x00ff00)
        for code in codes:
            lecture_seminar = None
            if code.lecture_id is not None:
                lecture_seminar = session.execute(select(Lecture).where(Lecture.id == code.lecture_id)).scalars().first()
            elif code.seminar_id is not None:
                lecture_seminar = session.execute(select(Seminar).where(Seminar.id == code.seminar_id)).scalars().first()
            embed.add_field(name=lecture_seminar.name, value=code.code, inline=False)
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="addcode")
    async def addcode(self, interaction: nextcord.Interaction, code: str, module_code: str,
                      is_seminar_lecture: int = nextcord.SlashOption(
                          name="is_seminar_lecture",
                          description="Is the code for a seminar or a lecture",
                          required=True,
                          choices={"seminar": 1, "lecture": 2}
                      )):
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

        module = await self.get_module(module_code, interaction)
        session = Session(self.engine)

        # Send a button to get Seminar/Lecture
        view = None
        if is_seminar_lecture == 1:
            # Send a button to get Seminar
            stmt = select(Seminar).where(Seminar.module_id == module.id)
            seminars = session.execute(stmt).scalars().all()
            if len(seminars) == 0:
                await interaction.response.send_message("Module has no seminars")
                return
            view = AddCodeView(code, engine=self.engine, seminars=seminars, module=module)
        elif is_seminar_lecture == 2:
            # Send a button to get Lecture
            stmt = select(Lecture).where(Lecture.module_id == module.id)
            lectures = session.execute(stmt).scalars().all()
            if len(lectures) == 0:
                await interaction.response.send_message("Module has no lectures")
                return
            view = AddCodeView(code, engine=self.engine, lectures=lectures, module=module)
        else:
            await interaction.response.send_message("Invalid option")
            return

        await interaction.response.send_message("Select a seminar/lecture", view=view)

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
        module = await self.get_module(module_code, interaction)
        session = Session(self.engine)

        stmt = select(Seminar).where(Seminar.module_id == module.id)
        seminars = session.execute(stmt).scalars().all()
        embed = nextcord.Embed(title="Seminars", description=f"List of all seminars for {module.name}", color=0x00ff00)
        for seminar in seminars:
            embed.add_field(name=seminar.name, value="ID: " + str(seminar.id), inline=False)
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
        module = await self.get_module(module_code, interaction)
        session = Session(self.engine)

        stmt = select(Lecture).where(Lecture.module_id == module.id)
        lectures = session.execute(stmt).scalars().all()
        embed = nextcord.Embed(title="Lectures", description=f"List of all lectures for {module.name}", color=0x00ff00)
        for lecture in lectures:
            embed.add_field(name=lecture.name, value="ID: " + str(lecture.id), inline=False)
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
        module = await self.get_module(module_code, interaction)

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
        module = await self.get_module(module_code, interaction)

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
            embed.add_field(name=command.name, value=command.description[:100] + "...", inline=False)
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(MainCog(bot))
