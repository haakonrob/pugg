import os
import logging
from .parsing import read_notes
from copy import deepcopy
# from .definitions import Note, Group
from .database import save_notes_db, load_notes_db
from .scoring import get_remembrance_probability, update_half_life


CACHE_PATH = '.'


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


def load_cache(dir):
    path = os.path.join(dir, '.pugg')
    return load_notes_db(path)


def main(dir):
    cache = load_cache(dir)
    if cache is None:
        return
    notes = read_notes(dir, cache)
    # notes = retrieve_and_initialise_metadata(notes)

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




