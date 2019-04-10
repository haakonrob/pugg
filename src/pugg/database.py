import os
import pickle
import logging
from collections import namedtuple
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean
from sqlalchemy import create_engine, or_ as OR, and_ as AND
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

# TODO add initialisation code for a directory (maybe with a database class?)

# TODO when setting up in a directory for the first time, the user should be asked to supply the --init flag.
    #  Checking for a valid directory should avoid stupid errors like calling pugg on a large filesystem



# engine = create_engine('sqlite:////tmp/pugg/db', echo=False)
# Base = declarative_base()
# session_factory = sessionmaker(bind=engine)
# db = session_factory()
# Base.metadata.create_all(engine)


# Database is represented by singleton class
class Database(object):
    _instance = None
    verbose = False
    Base = declarative_base()
    session_factory = None
    engine = None
    __session = None

    # On "creation" of a new instance, just copy over the existing global instance if it already exists
    def __new__(cls, db_path=None):
        if Database._instance is None:
            if db_path is None:
                raise ValueError("First time setup requires a path to the db file")
            self = object.__new__(cls)
            self.engine = create_engine(db_path, echo=self.verbose)
            self.session_factory = sessionmaker(bind=self.engine)
            self.Base.metadata.create_all(self.engine)
            self.__session = self.session_factory()
            Database._instance = self

        return Database._instance

    @property
    def session(self):
        return self.__session

    @property
    def scoped_session(self):
        return scoped_session(self.session_factory)()

    def commit(self, transaction):
        db = self.session

        # Delete all marked records
        for record in [*transaction.topics_to_delete,
                       *transaction.files_to_delete,
                       *transaction.cards_to_delete]:
            db.delete(record)
            db.commit()

        # Add new records
        db.add_all(transaction.new_records)
        db.commit()

        if (transaction.topics_to_delete or
                transaction.files_to_delete or
                transaction.cards_to_delete or
                transaction.new_records):

            logging.debug("Topics deleted: {}". format(transaction.topics_to_delete))
            logging.debug("Files deleted: {}". format(transaction.files_to_delete))
            logging.debug("Cards deleted: {}". format(transaction.cards_to_delete))
            logging.debug("New records: {}". format(transaction.new_records))


class Topic(Database.Base):
    __tablename__ = 'topics'
    path = Column(String, primary_key=True)
    parent_path = Column(String, ForeignKey('topics.path'))
    is_file = Column(Boolean)
    last_read = Column(Integer)
    real_path = Column(String)
    name = Column(String)
    children = relationship("Topic")

    def __repr__(self):
        return "Topic(name={}, path={}, children={})".format(self.name, self.path, [c.name for c in self.children])

    def __eq__(self, other):
        return self.real_path == other.real_path

    def __hash__(self):
        return hash(self.path)


# class File(Database.Base):
#     __tablename__ = 'files'
#     path = Column(String, primary_key=True)
#     name = Column(String)
#     topic_path = Column(String, ForeignKey('topics.path'))
#     topic = relationship("Topic")
#     last_read = Column(Integer, nullable=False)
#
#     def __repr__(self):
#         return "File(path={}, topic={})".format(self.path, self.topic_path)
#
#     def __eq__(self, other):
#         return self.path == other.path
#
#     def __hash__(self):
#         return hash(self.path)


class Card(Database.Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True)
    topic_path = Column(String, ForeignKey('topics.path'))
    topic = relationship(Topic)
    # file_path = Column(String, ForeignKey('files.path'))
    # file = relationship(File)

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

    # def __eq__(self, other):
    #     return (self.file_path == other.file_path) and (self.hash == other.hash)

    # def __hash__(self):
    #     return hash(self.file_path + self.hash)


class Transaction:
    new_records = set()
    topics_to_delete = set()
    files_to_parse = set()
    files_to_delete = set()
    cards_to_delete = set()

    def update_topics(transaction, topics):
        db = Database().session
        discovered_paths = [t.path for t in topics]

        # Mark new files for addition to the db
        seen_topics = db.query(Topic).all()
        for t in topics:
            if t not in seen_topics:
                transaction.new_records.add(t)

            # Mark any Topics in db for deletion if they are not in the currently discovered paths
            transaction.topics_to_delete.update(
                db.query(Topic).filter(AND(not Topic.is_file, Topic.path.notin_(discovered_paths))).all())

        # If there are deleted topics, mark the related records for deletion as well
        if transaction.topics_to_delete:
            transaction.cards_to_delete.update(
                db.query(Card).filter(Card.topic_path.in_(f.path for f in transaction.files_to_delete)).all())

        return transaction

    def update_files(transaction, files):
        db = Database().session
        # Decide which files should be marked for parsing by comparing the edit dates
        for f in files:
            lookup = db.query(Topic).filter(Topic == f).first()
            if not lookup:
                """ 
                    Event:      The file has not been seen before.
                    Action:     Add file to database.
                """
                transaction.new_records.add(f)
                transaction.files_to_parse.add(f)

            elif f.last_read != lookup.last_read:
                """
                    Event:      The file has been modified since the last read.
                    Action:     Mark file for re-parsing, mark old cards for deletion.
                """
                transaction.files_to_parse.add(f)
                lookup.last_read = f.last_read
                transaction.cards_to_delete.update(
                    db.query(Card).filter(Card.topic_path == f.path).all())
            else:
                """
                    Event:      The file has not been modified.
                    Action:     Leave as-is.
                """
                pass

        return transaction

    def update_cards(transaction, cards):
        # Try to match the new cards with some card about to be deleted, and adopt the metadata of the leaving card
        for c in cards:
            for other in transaction.cards_to_delete:
                # TODO try to replace with some SQL function
                if c.matches(other):
                    c.halflife = other.halflife
                    logging.info("Found match for {}".format(c))
                    break

        transaction.new_records.update(cards)

        return transaction

# TODO remove old database class
# class Database:
#     def __init__(self, cache_dir, first_time=False):
#         self.dbpath = os.path.join(cache_dir, 'db')
#         self.engine = create_engine('sqlite:///'+self.dbpath)
#
#         if first_time and not os.path.exists(cache_dir):
#             # self.initialise_notes_repo(cache_dir)
#             Base.metadata.create_all(self.engine)
#
#         if not os.path.exists(cache_dir) or not os.path.exists(self.dbpath):
#             print("Directory has not been initialised. If this is your notes directory, please move to the directory"
#                   "in your favourite shell and initialise it using the following command:\n\tpugg --init")
#             return None


# TODO remove old notes IO
# def save_notes_db(path, notes):
#     res = False
#     try:
#         with open(path, 'wb') as f:
#             pickle.dump(notes, f)
#             res = True
#             logging.debug("Successfully saved notes cache to {}".format(path))
#     except FileNotFoundError as e:
#         logging.error("{}\nUnable to save notes db to {}".format(e, path))
#     except TypeError as e:
#         logging.error("{}\nUnable to load notes db to {}".format(e, path))
#     finally:
#         return res
#
#
# def load_notes_db(path):
#     try:
#         with open(path, 'rb') as f:
#             notes = pickle.load(f)
#             logging.debug("Successfully loaded notes cache from {}".format(path))
#             return notes
#     except FileNotFoundError as e:
#         logging.error("{}\nUnable to load notes db from {}".format(e, path))
#         return None


