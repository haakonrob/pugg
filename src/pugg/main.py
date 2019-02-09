import logging
from notes_parser import read_notes
from copy import deepcopy
from definitions import Note, Group
from notes_io import save_notes_db, load_notes_db
from notes_scoring import initialise_metadata, get_remembrance_probability, update_half_life

CACHE_PATH = './.flashnotes/notes.db'


def setup_logging(log_level='INFO'):
    ext_logger = logging.getLogger("py.warnings")
    logging.captureWarnings(True)
    level = getattr(logging, log_level)
    logging.basicConfig(format="[%(asctime)s] %(levelname)s %(filename)s: %(message)s", level=level)
    if level <= logging.DEBUG:
        ext_logger.setLevel(logging.WARNING)


def retrieve_and_initialise_metadata(notes):
    notes = deepcopy(notes)
    cache = load_notes_db(CACHE_PATH)

    for path, note in notes.dfs():
        cached_note = cache[path] if cache is not None else None
        if cached_note is not None and 'metadata' in cached_note.__dict__ and cached_note.metadata is not None:
            logging.debug("Retrieved cache metadata for note at {}".format(path))
            note.metadata = deepcopy(cached_note.metadata)
        else:
            logging.debug("Initialised metadata for note at {}".format(path))
            notes[path] = initialise_metadata(note)

    return notes


def select(notes):
    return sorted(
        [(p, n, get_remembrance_probability(n)) for p, n in notes.dfs() ],
        key=lambda x: x[2])[0][0:2]


def display_print(note):
    print("")
    for face in note.faces:
        print(face)
        input("...\n")


def user_grade():
    while True:
        g = input("(p)erfect (g)ood  (o)k  (b)ad  (a)wful").lower()
        if g == 'p' or g == 'perfect' or g == '5':
            return 'perfect'
        elif g == 'g' or g == 'good' or g == '4':
            return 'perfect'
        elif g == 'o' or g == 'ok' or g == '3':
            return 'perfect'
        elif g == 'b' or g == 'bad' or g == '2':
            return 'perfect'
        elif g == 'a' or g == 'awful' or g == '1':
            return 'perfect'
        else:
            print("Invalid grade.")


setup_logging('DEBUG')

if __name__ == '__main__':
    notes = read_notes('./notes/')
    notes = retrieve_and_initialise_metadata(notes)

    try:
        while True:
            p, n = select(notes)
            display_print(n)
            g = user_grade()
            notes[p] = update_half_life(n, g)

    except KeyboardInterrupt:
        logging.info("Keyboard Interrupt, quitting program.")

    finally:
        ok = save_notes_db(CACHE_PATH, notes)
