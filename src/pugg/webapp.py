import os
import sys
from flask import Flask, render_template
from sqlalchemy.orm import scoped_session
from .database import session_factory, Topic, Card

this = sys.modules[__name__]
app = Flask('pugg',
            template_folder='web/templates',
            static_folder='web/static')
this.dir = None


def serve(notes_dir):
    this.dir = notes_dir
    app.run()


# TODO Define REST API

# TODO Retrieve card markdown, export to HTML w MathJax. Then display the card properly.

# TODO Add support for media like images and sounds?
#  Maybe the media can be loaded into some temp folder, or the real path can be injected into the template?


"""
Functionality:
    + *Browse* topics and notes by specifying their URL
    + *Revise* the weakest card within the current topic?
    + Start a study session where only cards/topics with a specific tag are selected
    + 
"""


@app.route('/')
@app.route('/browse/<path:path>')
def browse(path=''):
    db = scoped_session(session_factory)
    path = path[:-1] if path.endswith('/') else path
    topic = db.query(Topic).filter(Topic.path == path).first()

    if topic is None:
        return render_template('404.html', obj="topic", key=path)
    else:
        subtopics = db.query(Topic).filter(Topic.parent_path == path).all()
        cards = db.query(Card).filter(Card.topic_path == topic.path).all()
        return render_template('base.html', subtopics=subtopics, cards=cards)


@app.route('/revise/<int:id>')
def revise_card(id):
    db = scoped_session(session_factory)
    card = db.query(Card).filter(Card.id == id).first()
    if card:
        return render_template('card.html', card=card)
    else:
        return render_template('404.html', obj="card", key=id)
