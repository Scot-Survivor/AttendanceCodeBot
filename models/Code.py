import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from . import Base


class Code(Base):
    __tablename__ = 'codes'
    id = Column(Integer, primary_key=True)
    code = Column(String(5), nullable=False)

    status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.now)

    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    lecture_id = Column(Integer, ForeignKey('lectures.id'), nullable=True)
    seminar_id = Column(Integer, ForeignKey('seminars.id'), nullable=True)

    def __repr__(self):
        return f"Module(name='{self.name}', description='{self.description}', status={self.status}, created_at='{self.created_at}', updated_at='{self.updated_at}')"
