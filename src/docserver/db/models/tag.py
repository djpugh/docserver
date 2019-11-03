from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from docserver.db.models.base import Model


association_table = Table('association', Model.metadata,
                          Column('tag_id', Integer, ForeignKey('tag.id')),
                          Column('package_id', Integer, ForeignKey('package.id')))


class Tag(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    packages = relationship(
        "Package",
        secondary=association_table,
        back_populates="tags")

    def __repr__(self):
        return f'Tag<{self.name}>'
