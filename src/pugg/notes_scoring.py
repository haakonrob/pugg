from math import exp, log
from time import time
from random import random
from definitions import Note, Store


"""
Each note is given an expected 'half-life', meaning the time until the remembrance probability is 50%.
This gives us control over the time when the note will have to be reviewed again, as well as still allowing
us to rank notes that will be reviewed around the same time using the remembrance probability. Furthermore, the 
probability decays exponentially with time, which is a very reasonable assumption that is frequently made when
studying memory. This model is very simple to apply to note review: if the note was remembered well, increase the 
half-life. If it went badly, decrease it. 

The update law is just implemented as a multiplication for now. This is something that could be optimised over time 
by analysing what the actual remembrance distribution looks like. By looking at histogram counts of successfully 
remembered and forgotten notes, and comparing this to the expected counts, we can see if our update law is too
optimistic or not.
"""


grades = {
    'perfect': 3,
    'good': 2,
    'ok': 1,
    'bad': 0.5,
    'awful': 0.333,
}


def initialise_metadata(note):
    return Note(name=note.name,
                faces=note.faces,
                metadata=Store(half_life=1,
                               last_reviewed=time()))


def update_half_life(note, grade):
    # The randomness helps make sure that notes won't 'clump up', having the same decay rates leading
    # to repating study sessions
    multiplier = grades[grade]
    half_life = note.metadata.half_life if note.metadata.half_life is not None else 1
    last_reviewed = note.metadata.last_reviewed if note.metadata.last_reviewed is not None else time()
    return Note(name=note.name,
                faces=note.faces,
                metadata=Store(half_life=max(1.0, half_life * (multiplier + 0.05 * (random() - 0.5))),
                               last_reviewed=last_reviewed))


def get_remembrance_probability(note):
    t = time() - note.metadata.last_reviewed  # seconds
    b = log(2)/(note.metadata.half_life*24*60*60)  # half_life is set in days, for human readablility
    return exp(-b*t)
