import os
import sys
import click
import logging
from . import database as DB
from .database import Database, Transaction, DEBUGGING_DB_PATH
from .parsing import read_notes, walk_notes, parse_files
from . import webapp


@click.command()
@click.argument('keywords', nargs=-1)
@click.option('--init', is_flag=True, help="Initialises a notes directory for the first time.")
@click.option('-w', '--web', is_flag=True, help="Starts the web server")
@click.option('-v', default=0, count=True, help="Number of v's sets the logging level. Examples: -v -> DEBUG, -vv -> INFO, etc")
@click.option('--dir', default=os.getcwd(), help="Directory where your notes can be found. "
                                                 "Defaults to the current directory")
def pugg(keywords, init, web, v, dir):
    """
    Program that helps you review your notes.
    KEYWORDS are the topics that you want to study, and it must match some directory in your notes tree.
    You can write it in all lowercase, and spaces can be written as '_'.
    Write * if you want to review cards from all notes.

    Pugg recursively explores your notes directory, parsing any Markdown files it finds and extracting flashcards from
    them. If you want Pugg to convert some text to a flashcard, wrap it in a BlockQuote (put '>' at the start of each line).
    and separate the text on the front and back of the card with a single empty line.

    Enjoy!

    """
    dir = os.path.realpath(dir)

    topics_discovered, files_discovered = walk_notes(dir)

    db = Database(DEBUGGING_DB_PATH)
    transaction = compute_transaction(topics_discovered, files_discovered, root=dir)
    db.commit(transaction)

    if web:
        webapp.serve(dir, keywords)


# dir = validate_dir(dir)
# if dir is None:
#     print("This is not a pugg subdirectory. Navigate to a pugg directory or specify one using the --dir argument.")
#     return
# dbpath = os.path.join(dir, '.pugg/db')


def validate_dir(path):
    dbpath = os.path.join(path, '.pugg/db')
    if os.path.exists(dbpath):
        return path

    else:
        parent = os.path.realpath(os.path.join(path, '..'))
        if parent == path:
            # Reached the top directory
            return None
        else:
            return validate_dir(parent)


def compute_transaction(topics, files, root):
    transaction = Transaction()

    # TODO the order of these shouldn't matter, but its confusing. Ideally there should be a method that takes
    #  in all discovered paths, and handles them according to whether they're directories or files, which is really
    #  the only distinction between a Topic, and a File (collection of Cards)
    transaction.update_topics(topics)
    transaction.update_files(files)

    cards = parse_files(transaction.files_to_parse, root)

    transaction.update_cards(cards)

    return transaction


def setup_logging(verbosity):
    print("Logging:", verbosity)
    if verbosity < 6:
        log_level = ['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'][verbosity]
        ext_logger = logging.getLogger("py.warnings")
        logging.captureWarnings(True)
        level = getattr(logging, log_level)
        logging.basicConfig(format="[%(asctime)s] %(levelname)s %(filename)s: %(message)s", level=level)
        if level <= logging.DEBUG:
            ext_logger.setLevel(logging.WARNING)
