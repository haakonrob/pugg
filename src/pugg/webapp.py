import os
import sys
from flask import Flask, render_template, send_from_directory
from .database import Database, Topic, File, Card, OR, AND


########################################################################################################################
# TODO For browsing cards, use Bootstraps Card element!
# TODO display current filters using buttons, click on them to make them disappear
#
#
#
#
#
########################################################################################################################

this = sys.modules[__name__]
web_folder = os.path.join(os.path.dirname(__file__), 'web')
template_folder = os.path.join(web_folder, 'templates')
static_folder = os.path.join(web_folder, 'static')
revision_cards = []
this.dir = None
this.curr_view = None
active_cards = []

app = Flask('pugg',
            template_folder=template_folder,
            static_folder=static_folder)


def serve(notes_dir, keywords):
    this.dir = notes_dir
    this.keywords = keywords
    this.active_cards = []
    update_cards()
    app.run()


def update_cards():
    db = Database().session
    active_cards = db.query(Card).all()
    pass


@app.route('/')
@app.route('/browse/<path:path>')
def browse(path=''):
    db = Database().session
    path = path[:-1] if path.endswith('/') else path
    topic = db.query(Topic).filter(Topic.path == path).first()

    if topic is None:
        return render_template('404.html', obj="topic", key=path)
    else:
        subtopics = db.query(Topic).filter(Topic.parent_path == path).all()
        cards = db.query(Card).filter(Card.topic_path == topic.path).all()
        return render_template('browse.html', subtopics=subtopics, cards=cards)


@app.route("/revise/next")
def get_next_card():
    db = Database().session


@app.route('/revise/<int:id>')
def revise_card(id):
    db = Database().session
    card = db.query(Card).filter(Card.id == id).first()

    if card:
        this.curr_view = card.topic.real_path
        return render_template('card.html', card=card)
    else:
        return render_template('404.html', obj="card", key=id)


# @app.route('/revise/random')
# def choose_random_card_for_revision():
#

@app.route('/assets/<path:path>')
def assets(path):
    print(os.path.dirname(path), os.path.basename(path))
    return send_from_directory('/'+os.path.dirname(path), os.path.basename(path))
