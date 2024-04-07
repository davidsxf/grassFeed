from sqlalchemy import Column, Integer, String, Float
from database import Base

class Feeds(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    weight_range = Column(String, index=True)
    t_range = Column(String, index=True)
    weight_min = Column(Float)
    weight_max = Column(Float)
    t_min = Column(Float)
    t_max = Column(Float)
    coe_min = Column(Float)
    coe_max = Column(Float)
    fcr = Column(Float)
    