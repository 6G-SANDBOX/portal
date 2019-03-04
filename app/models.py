from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import app, login
from time import time
import jwt
from datetime import datetime


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    experiments = db.relationship('Experiment', backref='author', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.id}, Username {self.username}, Email {self.email}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    def user_experiments(self):
        exp = Experiment.query.filter_by(user_id=self.id)
        return exp.order_by(Experiment.id.desc())

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def serialization(self):
        experiments_ids = []
        for exp in self.user_experiments():
            experiments_ids.append(exp.id)
        dictionary = {'Id': self.id, 'UserName': self.username, 'Email': self.email, 'Experiments': experiments_ids}
        return dictionary


class Experiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    executions = db.relationship('Execution', backref='experiment', lazy='dynamic')

    def __repr__(self):
        return f'<Experiment {self.id}, Name {self.name}, User_id {self.user_id}>'

    def experiment_executions(self):
        exp = Execution.query.filter_by(experiment_id=self.id)
        return exp.order_by(Execution.id.desc())

    def serialization(self):
        executions_ids = []
        for exe in self.experiment_executions():
            executions_ids.append(exe.id)
        dictionary = {'Id': self.id, 'Name': self.name, 'User': User.query.get(self.user_id).serialization(), 'Executions': executions_ids}
        return dictionary


class Execution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    start_time = db.Column(db.DATETIME)
    end_time = db.Column(db.DATETIME)
    status = db.Column(db.String(32))

    def __repr__(self):
        return f'<Execution {self.id}, Experiment_id {self.experiment_id}, Start_time {self.start_time}, End_time {self.end_time}, Status {self.status}>'
