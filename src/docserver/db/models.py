from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from docserver import db


class Language(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    packages = relationship('Package', backref='language', lazy=True)

    def __repr__(self):
        return f'<Language {self.name}>'


class Package(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    language_id = Column(Integer, ForeignKey('language.id'), nullable=False)
    repository = Column(String(300), unique=True, nullable=False)
    description = Column(String(800), nullable=True)

    def __repr__(self):
        return f'<Package {self.name} ({self.language})>'
