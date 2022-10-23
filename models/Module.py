import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from . import Base


class Module(Base):
    __tablename__ = 'modules'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    module_code = Column(String(20), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return f"Module(name='{self.name}', description='{self.description}', status={self.status}, created_at='{self.created_at}', updated_at='{self.updated_at}')"
