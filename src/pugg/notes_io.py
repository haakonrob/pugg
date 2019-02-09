import pickle
import logging


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


