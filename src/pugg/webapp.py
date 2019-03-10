import os
import sys
from flask import Flask, render_template, send_from_directory
from sqlalchemy.orm import scoped_session
from .database import session_factory, Topic, Card

this = sys.modules[__name__]
web_folder = os.path.join(os.path.dirname(__file__), 'web')
temp_view_folder = os.path.join(web_folder, 'tempview')
template_folder = os.path.join(web_folder, 'templates')
static_folder = os.path.join(web_folder, 'static')

app = Flask('pugg',
            template_folder=template_folder,
            static_folder=static_folder)
this.dir = None
this.curr_view = None

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
        return render_template('browse.html', subtopics=subtopics, cards=cards)


@app.route('/revise/<int:id>')
def revise_card(id):
    db = scoped_session(session_factory)
    card = db.query(Card).filter(Card.id == id).first()

    if card:
        this.curr_view = card.topic.real_path
        #
        # # Create link to local folder of file, gives access to assets like images etc
        # if os.path.exists(temp_view_folder):
        #     os.remove(temp_view_folder)
        # os.symlink(card.topic.real_path, temp_view_folder, target_is_directory=True)

        return render_template('card.html', card=card)
    else:
        return render_template('404.html', obj="card", key=id)


@app.route('/assets/<path:path>')
def assets(path):
    print(os.path.dirname(path), os.path.basename(path))
    return send_from_directory('/'+os.path.dirname(path), os.path.basename(path))
