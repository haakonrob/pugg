import os
import click
import logging
# from .main_old import main
from .database import db, Card, File, Topic
from .parsing import read_notes2, walk_notes, parse_files



@click.command()
@click.argument('topic', default='all')
@click.option('--init', is_flag=True, help="Initialises a notes directory for the first time.")
@click.option('-v', count=True, help="Number of v's sets the logging level. Examples: -v -> DEBUG, -vv -> INFO, etc")
@click.option('--dir', default=os.getcwd(), help="Directory where your notes can be found. "
                                                 "Defaults to the current directory")
def pugg(topic, init, v, dir):
    """
    Program that helps you review your notes.
    TOPIC is the topic that you want to study, and it must match some directory in your notes tree.
    You can write it in all lowercase, and spaces can be written as '_'.
    Write * if you want to review cards from all notes.

    Pugg recursively explores your notes directory, parsing any Markdown files it finds and extracting flashcards from
    them. If you want Pugg to convert some text to a flashcard, wrap it in a BlockQuote (put '>' at the start of each line).
    and separate the text on the front and back of the card with a single empty line.

    Enjoy!

    """
    setup_logging(v)

    # TODO when setting up in a directory for the first time, the user should be asked to supply the --init flag to
    #  ensure that they aren't going to walk across the whole filesystem

    # TODO pugg needs to search for the .pugg folder to get the previous state, should search parent folders too.
    #  similar to git

    # TODO Locate all files first, along with their last read date, then filter them based on the file database.
    #  After this is done, the reduced list of files can be read and parsed.

    # markdown_files = [f for f in walk(dir) if f.ext =='.md']
    # markdown_files = db.filter(markdown_files, 'last_updated')
    # notes = parse_files(markdown_files)
    # db.update(Card, notes)
    # db.update(File, files)
    #
    # cards = db.select(Card, topic=topic)
    # i = min(range(len(cards)), key=lambda i: cards[i].
    # weakest_card = cards.pop(i)


    """
    Loading strategies for persistence:
        Topic loading:
        1) A folder not in db is found
            Add it to the database
        2) A folder in db is found
            Do nothing
        3) A folder in db is not found, 
            Mark for deletion, mark related files and cards for deletion
        4) A folder not in db is not found
            ???
            
        File loading:
        1) A file not in db is found 
            Add to db and mark for extraction
        2) A file in db is found, edit time matches
            Do nothing
        3) A file in db is found, edit time does not match
            Mark related cards for deletion, mark file for extraction.
        4) A file in db has not been found
            Mark file for deletion, mark related cards for deletion
        
        Card extraction:
        1) A card not in db is found, does not match anything
            Add to db
        2) A card not in db is found, but matches some other card marked for deletion
            Update card in db   
        3) A card in db is found
            Do nothing
        4) A card in db is found, edit time does not match
            Mark related cards for deletion, mark file for extraction.
        5) A card in db has not been found
            Mark file for deletion, mark related cards for deletion
        
        Full update:
            Once all metadata is transferred, deletions are commited, 
            then new records are inserted
    """
    topics, files = walk_notes(dir)
    discovered_paths = [t.path for t in topics]
    topics_to_delete = set()
    files_to_parse = set()
    files_to_delete = set()
    cards_to_delete = set()
    new_records = set()

    # cached_topics = {t.path: t for t in db.query(Topic).all()}
    # for t in topics:
    #     if t.path not in cached_topics:
    #         # New record
    #     elif

    # Mark all records not consistent with the current directory for deletion
    cached_topics = {f.path: f for f in db.query(Topic).all()}
    # db.add_all(topics)
    for t in topics:
        if t not in db.query(Topic).all():
            new_records.add(t)
    topics_to_delete.update(
        db.query(Topic).filter(Topic.path.notin_(discovered_paths)).all())
    if topics_to_delete:
        files_to_delete.update(
            db.query(File).filter(File.topic_path.in_(t.path for t in topics_to_delete)).all())
        cards_to_delete.update(
            db.query(Card).filter(Card.file_path.in_(f.path for f in files_to_delete)).all())

    # Decide which files should be marked for extraction
    cached_files = {f.path: f for f in db.query(File).all()}

    for f in files:
        lookup = db.query(File).filter(File == f).first()
        if not lookup:
            """ 
                Event:      The file has not been seen before.
                Action:     Add file to database.
            """
            new_records.add(f)
            files_to_parse.add(f)

        elif f.last_read != lookup.last_read:
            """
                Event:      The file has been modified since the last read.
                Action:     Mark file for re-parsing, mark old cards for deletion.
            """
            files_to_parse.add(f)
            lookup.last_read = f.last_read
            cards_to_delete.update(
                db.query(Card).filter(Card.file_path == f.path).all())
        else:
            """
                Event:      The file has not been modified.
                Action:     Leave as-is.
            """
            # File is in db, and has not changed.
            pass

    cards = parse_files(files_to_parse)
    for c in cards:
        # If matches some card about to be deleted, update halflife, then add
        for other in cards_to_delete:
            # TODO try to replace with some SQL function
            if c.matches(other):
                c.halflife = other.halflife
                logging.info("Found match for {}".format(c))
                break

    new_records.update(cards)

    # Delete all marked records
    for record in [*topics_to_delete, *files_to_delete, *cards_to_delete]:
        db.delete(record)
    db.commit()

    # Add new records
    db.add_all(new_records)
    db.commit()

    logging.debug("Topics deleted: {}". format(topics_to_delete))
    logging.debug("Files deleted: {}". format(files_to_delete))
    logging.debug("Cards deleted: {}". format(cards_to_delete))
    logging.debug("New records: {}". format(new_records))

    # All possible changes have been added to the database!
    # main(dir)


def setup_logging(verbosity):
    if verbosity < 6:
        log_level = ['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'][verbosity]
        ext_logger = logging.getLogger("py.warnings")
        logging.captureWarnings(True)
        level = getattr(logging, log_level)
        logging.basicConfig(format="[%(asctime)s] %(levelname)s %(filename)s: %(message)s", level=level)
        if level <= logging.DEBUG:
            ext_logger.setLevel(logging.WARNING)
