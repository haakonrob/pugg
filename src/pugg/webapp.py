import os
import sys
from flask import Flask, render_template
from sqlalchemy.orm import scoped_session
from .database import session_factory, Topic, Card

this = sys.modules[__name__]
app = Flask('pugg', template_folder='web/templates')
this.dir = None


def serve(notes_dir):
    this.dir = notes_dir
    app.run()


@app.route('/')
@app.route('/<path:path>')
def whatever(path=''):
    db = scoped_session(session_factory)
    path = path[:-1] if path.endswith('/') else path
    topic = db.query(Topic).filter(Topic.path == path).first()

    if topic is None:
        return render_template('404.html', topic=path)
    else:
        subtopics = db.query(Topic).filter(Topic.parent_path == path).all()
        cards = db.query(Card).filter(Card.topic_path == topic.path).all()
        print(topic.path)
        return render_template('base.html', subtopics=subtopics, cards=cards)
