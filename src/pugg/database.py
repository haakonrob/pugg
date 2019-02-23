import os
import pickle
import logging
from collections import namedtuple
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine

if not os.path.exists('/tmp/pugg/'):
    os.mkdir('/tmp/pugg/')
engine = create_engine('sqlite:////tmp/pugg/db', echo=False)
Base = declarative_base()
session_factory = sessionmaker(bind=engine)
db = session_factory()


class Topic(Base):
    __tablename__ = 'topics'
    path = Column(String, primary_key=True)
    real_path = Column(String)
    parent_path = Column(String, ForeignKey('topics.path'))
    name = Column(String)
    children = relationship("Topic")

    def __repr__(self):
        return "Topic(name={}, path={}, children={})".format(self.name, self.path, [c.name for c in self.children])

    def __eq__(self, other):
        return self.path == other.path

    def __hash__(self):
        return hash(self.path)


class File(Base):
    __tablename__ = 'files'
    path = Column(String, primary_key=True)
    name = Column(String)
    topic_path = Column(String, ForeignKey('topics.path'))
    topic = relationship("Topic")
    last_read = Column(Integer, nullable=False)

    def __repr__(self):
        return "File(path={}, topic={})".format(self.path, self.topic_path)

    def __eq__(self, other):
        return self.path == other.path

    def __hash__(self):
        return hash(self.path)


class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True)
    topic_path = Column(String, ForeignKey('topics.path'))
    topic = relationship(Topic)
    file_path = Column(String, ForeignKey('files.path'))
    file = relationship(File)

    hash = Column(String, nullable=False)
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    halflife = Column(Float, nullable=False)
    last_reviewed = Column(Integer, nullable=False)

    def matches(self, other):
        """
        Weak form of equality. If only one of (file_path, front, back) has changed, then the cards
        match. This is used to allow users to change one aspect of a card without consequence.
        """
        # This allows one of the following to change: front changes, back changes, path changes, without affecting the
        # the score.
        return ((self.front == other.front) + (self.back == other.back) + (self.file_path == other.file_path)) >= 2

    def __repr__(self):
        return "Card(id={}, front={}, topic_path={})".format(self.id, self.front, self.topic_path)

    def __eq__(self, other):
        return (self.file_path == other.file_path) and (self.hash == other.hash)

    def __hash__(self):
        return hash(self.file_path + self.hash)


Base.metadata.create_all(engine)


class Database:
    def __init__(self, cache_dir, first_time=False):
        self.dbpath = os.path.join(cache_dir, 'db')
        self.engine = create_engine('sqlite:///'+self.dbpath)

        if first_time and not os.path.exists(cache_dir):
            # self.initialise_notes_repo(cache_dir)
            Base.metadata.create_all(self.engine)

        if not os.path.exists(cache_dir) or not os.path.exists(self.dbpath):
            print("Directory has not been initialised. If this is your notes directory, please move to the directory"
                  "in your favourite shell and initialise it using the following command:\n\tpugg --init")
            return None


def save_notes_db(path, notes):
    res = False
    try:
        with open(path, 'wb') as f:
            pickle.dump(notes, f)
            res = True
            logging.debug("Successfully saved notes cache to {}".format(path))
    except FileNotFoundError as e:
        logging.error("{}\nUnable to save notes db to {}".format(e, path))
    except TypeError as e:
        logging.error("{}\nUnable to load notes db to {}".format(e, path))
    finally:
        return res


def load_notes_db(path):
    try:
        with open(path, 'rb') as f:
            notes = pickle.load(f)
            logging.debug("Successfully loaded notes cache from {}".format(path))
            return notes
    except FileNotFoundError as e:
        logging.error("{}\nUnable to load notes db from {}".format(e, path))
        return None


