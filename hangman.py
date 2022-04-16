import random

import flask
from flask_sqlalchemy import SQLAlchemy
import os, sys
import webbrowser

app = flask.Flask(__name__)

# Database

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hangman.db'
db = SQLAlchemy(app)


def base_path(path):
    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)


# Model

def random_pk():
    return random.randint(1e9, 1e10)

def random_word():
    words = [line.strip() for line in open('words.txt') if len(line) > 10]
    return random.choice(words).upper()

class Game(db.Model):
    pk = db.Column(db.Integer, primary_key=True, default=random_pk)
    word = db.Column(db.String(50), default=random_word)
    tried = db.Column(db.Unicode, default='')
    player = db.Column(db.String(50))

    def __init__(self, player):
        self.player = player.capitalize()

    @property
    def errors(self):
        return ''.join(set(self.tried) - set(self.word))

    @property
    def current(self):
        return ''.join([c if c in self.tried else '_' for c in self.word])

    @property
    def points(self):
        return 100 + 2*len(set(self.word)) + len(self.word) - 10*len(self.errors)

    @property
    def real_errors(self):
        str1 = ""
        for i in range(0,len(self.tried)):
            if self.tried[i] in set(self.word):
                str1 = self.tried[i:]
                break
        return ''.join(set(str1) - set(self.word))

    # Play

    def try_letter(self, letter):
        if not self.finished:
            if len(letter) == 1 and letter not in self.tried:
                self.tried += letter
                db.session.commit()
            elif letter == self.word:
                self.tried = self.word
                db.session.commit()
            elif letter != self.word:
                for i in range(65,91):
                    if chr(i) not in set(self.word.upper()) and len(self.errors)<6:
                        self.tried += chr(i)
                db.session.commit()


    # Game status

    @property
    def won(self):
        return self.current == self.word

    @property
    def lost(self):
        return len(self.real_errors) >= 6

    @property
    def finished(self):
        return self.won or self.lost


# Controller

@app.route('/')
def home():
    games = sorted(
        [game for game in Game.query.all() if game.won],
        key=lambda game: -game.points)[:10]
    return flask.render_template('home.html', games=games)

@app.route('/play')
def new_game():
    player = flask.request.args.get('player')
    game = Game(player)
    db.session.add(game)
    db.session.commit()
    return flask.redirect(flask.url_for('play', game_id=game.pk))

@app.route('/play/<game_id>', methods=['GET', 'POST'])
def play(game_id):
    game = Game.query.get_or_404(game_id)

    if flask.request.method == 'POST':
        letter = flask.request.form['letter'].upper()
        if letter.isalpha() and (len(letter) == 1 or len(letter) == len(game.word)):
            game.try_letter(letter)

    if flask.request.is_xhr:
        return flask.jsonify(current=game.current,
                             errors=game.errors,
                             finished=game.finished,
                             real_errors= game.real_errors)
    else:
        return flask.render_template('play.html', game=game)

# Main

if __name__ == '__main__':
    app.run()
