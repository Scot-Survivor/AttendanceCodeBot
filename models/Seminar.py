import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from . import Base


class Seminar(Base):
    __tablename__ = 'seminars'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    module_id = Column(Integer, ForeignKey('modules.id'))

    def __repr__(self):
        return f"Lecture(name='{self.name}', description='{self.description}', status={self.status}, created_at='{self.created_at}', updated_at='{self.updated_at}')"
