import random
import time

import flask
from flask_sqlalchemy import SQLAlchemy
import os, sys
import webbrowser

app = flask.Flask(__name__)

# Changing directory

def base_path(path):
    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir =  os.path.abspath(os.path.dirname(__file__))
    return os.path.join(basedir, path)

# Database 

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'hangman.db')
db = SQLAlchemy(app)

# Model

def random_pk():
    return random.randint(1e9, 1e10)

# Selecting random word from words.txt according to the difficulty

def random_word(difficulty):
    if difficulty == "EASY":
        words = [line.strip() for line in open(base_path('words.txt')) if 4 <= len(line.strip()) <= 6]
    elif difficulty == "MEDIUM":
        words = [line.strip() for line in open(base_path('words.txt')) if 6 < len(line.strip()) <= 9]
    else:
        words = [line.strip() for line in open(base_path('words.txt')) if 9 < len(line.strip())]
    return random.choice(words).upper()

class Game(db.Model):
    pk = db.Column(db.Integer, primary_key=True, default=random_pk)
    word = db.Column(db.String(50), default=random_word("EASY"))
    tried = db.Column(db.String(50), default='')
    player = db.Column(db.String(50))

    # Initializing the game

    def __init__(self, player, difficulty):
        self.player = player.capitalize()
        self.difficulty = difficulty
        self.word = random_word(difficulty.upper())

    # Returns the String of letters the user got wrong

    @property
    def errors(self):
        return ''.join(set(self.tried) - set(self.word))

    # Returns the current state of the game

    @property
    def current(self):
        return ''.join([c if c in self.tried else '_' for c in self.word])

    # Returns the points earned by the player

    @property
    def points(self):
        return 100 + 2*len(set(self.word)) + len(self.word) - 10*len(self.real_errors)

    # Returns the number of errors the player made after the user got the first letter right

    @property
    def real_errors(self):
        str1 = ""
        for i in range(0, len(self.tried)):
            if self.tried[i] in set(self.word):
                str1 = self.tried[i:]
                break
        return ''.join(set(str1) - set(self.word))

    # Play
    # Checks if the input is a letter and if it is in the word
    # Else checks if the input is of the same length as the current word and if it is the same

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
# Sorts the database according to points and divides them according to difficulty 

@app.route('/')
def home():
    games_easy = sorted(
        [game for game in Game.query.all() if game.won and 4 <= len(game.current) <= 6],
        key=lambda game: -game.points)[:5]
    games_medium = sorted(
        [game for game in Game.query.all() if game.won and 6 < len(game.current) <= 9],
        key=lambda game: -game.points)[:5]
    games_hard = sorted(
        [game for game in Game.query.all() if game.won and len(game.current) > 9],
        key=lambda game: -game.points)[:5]
    return flask.render_template('home.html', games_easy=games_easy, games_medium = games_medium, games_hard = games_hard)

# Starts a new game with player name and difficulty

@app.route('/play')
def new_game():
    player = flask.request.args.get('player')
    difficulty = flask.request.args.get('difficulty_level')
    game = Game(player, difficulty)
    db.session.add(game)
    db.session.commit()
    time.sleep(2)
    return flask.redirect(flask.url_for('play', game_id=game.pk))

# 

@app.route('/play/<game_id>', methods=['GET', 'POST'])
def play(game_id):
    game = Game.query.get_or_404(game_id)

    if flask.request.method == 'POST':
        letter = flask.request.form['letter'].upper()

        # Checking if the letter is an alphabet and length of the input is 1 or the length of the word
        if letter.isalpha() and (len(letter) == 1 or len(letter.strip()) == len(game.word)):
            game.try_letter(letter.strip())

    if flask.request.is_xhr:
        return flask.jsonify(current=game.current,
                             errors=game.errors,
                             finished=game.finished,
                             real_errors=game.real_errors)
    else:
        return flask.render_template('play.html', game=game)

# Main

if __name__ == '__main__':

    # Opening the web address of the game
    webbrowser.open_new_tab("http://127.0.0.1:5000/")

    # Changing the directory
    os.chdir(base_path(''))

    # Runnning the game
    app.run()