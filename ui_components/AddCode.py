import typing
import nextcord
from models.Seminar import Seminar
from models.Lecture import Lecture
from models.Module import Module
from models.Code import Code
from sqlalchemy import select
from sqlalchemy.orm import Session


class CodeDropdown(nextcord.ui.Select):
    def __init__(self, code: str, engine, module: Module, seminars: typing.List[Seminar] = None, lectures: typing.List[Lecture] = None):
        if seminars is None and lectures is None:
            raise ValueError("You must pass either seminars or lectures")
        self.seminars = seminars
        self.lectures = lectures
        self.module = module
        self.engine = engine
        self.code = code

        options = []
        if seminars is not None:
            for seminar in seminars:
                options.append(nextcord.SelectOption(label=seminar.name, value=seminar.name))
        if lectures is not None:
            for lecture in lectures:
                options.append(nextcord.SelectOption(label=lecture.name, value=lecture.name))

        super(CodeDropdown, self).__init__(placeholder="Select a seminar/lecture", min_values=1, max_values=1, options=options)

    def check_if_code_exists(self, session: Session):
        stmt = select(Code).where(Code.code == self.code)
        return session.execute(stmt).scalars().first() is not None

    async def callback(self, interaction: nextcord.Interaction):
        with Session(self.engine) as session:
            if not self.check_if_code_exists(session):
                stmt = select(Seminar).where(Seminar.id == self.values[0])
                obj_seminar = session.execute(stmt).scalars().first()
                stmt = select(Lecture).where(Lecture.name == self.values[0])
                obj_lecture = session.execute(stmt).scalars().first()
                if obj_seminar is None and obj_lecture is None:
                    await interaction.response.send_message("Seminar or lecture does not exist. Please ask an admin to create it")
                    return

                if obj_seminar is not None:
                    obj_code = Code(code=self.code, module_id=self.module.id, seminar_id=obj_seminar.id)
                elif obj_lecture is not None:
                    obj_code = Code(code=self.code, module_id=self.module.id, lecture_id=obj_lecture.id)

                session.add(obj_code)
                session.commit()
            else:
                await interaction.response.send_message("Code already exists")
                return

        await interaction.response.send_message(f"Added code! {self.code} for {self.module.name}")


class AddCodeView(nextcord.ui.View):
    def __init__(self, code: str, engine, module: Module, seminars: typing.List[Seminar] = None, lectures: typing.List[Lecture] = None):
        super().__init__()
        self.add_item(CodeDropdown(code, engine, module, seminars, lectures))
