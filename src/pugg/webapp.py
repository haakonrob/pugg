import os
import sys
from types import SimpleNamespace
from flask import Flask, render_template, redirect, send_from_directory
from .database import Database, Topic, Card, OR, AND
from .scoring import update_half_life, get_remembrance_probability


########################################################################################################################
# TODO For browsing cards, use Bootstraps Card element!
# TODO display current filters using buttons, click on them to make them disappear
#
#
#
#
#
########################################################################################################################

state = SimpleNamespace()
web_folder = os.path.join(os.path.dirname(__file__), 'web')

template_folder = os.path.join(web_folder, 'templates')
static_folder = os.path.join(web_folder, 'static')

state.dir = None
state.active_cards = []
state.scores = {}
state.dir = ""
state.keywords = []

app = Flask('pugg',
            template_folder=template_folder,
            static_folder=static_folder)


def serve(notes_dir, keywords):
    state.dir = notes_dir
    state.keywords.append(keywords)
    reset_state()
    try:
        app.run()
    finally:
        if state.scores:
            commit_state()


def reset_state():
    state.scores = {}
    if state.keywords:
        state.active_cards = filter_cards()


def commit_state():
    db = Database().scoped_session
    cards = db.query(Card.halflife).filter(Card.id.in_(state.scores.keys())).all()

    for card in cards:
        card.halflife = update_half_life(card.halflife, state.scores[card.id])

    db.commit()


def filter_cards():
    # Searches for cards using the keywords specified by the user.
    db = Database().scoped_session
    return db.query(Card).filter(AND(Card.topic_path.contains(v) for v in state.keywords)).all()


@app.route('/', methods=['GET'])
def home_page():
    return render_template('browse.html', state=state)


@app.route('/browse/<path:path>', methods=['GET'])
def browse(path=''):
    db = Database().scoped_session
    path = path[:-1] if path.endswith('/') else path
    topic = db.query(Topic).filter(Topic.path == path).first()

    if topic is None:
        return render_template('404.html', obj="topic", key=path)
    else:
        subtopics = db.query(Topic).filter(Topic.parent_path == path).all()
        cards = db.query(Card).filter(Card.topic_path == topic.path).all()
        return render_template('browse.html', subtopics=subtopics, cards=cards)


@app.route("/revise/next", methods=['GET'])
def revise_next_card():
    if state.active_cards:
        state.curr_card = state.active_cards.pop()
        return render_template('revise.html', state=state)
    else:
        commit_state()
        reset_state()
        return redirect('/')


@app.route('/revise/<int:id>', methods=['GET'])
def revise_card(id):
    db = Database().scoped_session
    card = db.query(Card).filter(Card.id == id).first()

    if card:
        return render_template('revise.html', state=state)
    else:
        return render_template('404.html', obj="card", key=id)


@app.route("/scores/<int:id>/<int:score>", methods=['POST'])
def score_card(id, score):
    state.scores[id] = score


@app.route('/assets/<path:path>', methods=['GET'])
def assets(path):
    print(os.path.dirname(path), os.path.basename(path))
    return send_from_directory('/'+os.path.dirname(path), os.path.basename(path))


if Database._instance is None:
    db = Database('sqlite:////tmp/pugg/db')
    state.keywords.append("mathematics")
    state.dir = '/home/haakonrr/OneDrive/notes/'
    reset_state()
