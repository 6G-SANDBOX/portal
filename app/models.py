from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login
from time import time
from flask import current_app
from sqlalchemy.types import TypeDecorator, VARCHAR
import json
import jwt
from Helper import Config as HelperConfig


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    @property
    def python_type(self):
        pass

    def process_literal_param(self, value, dialect):
        pass

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    organization = db.Column(db.String(32))
    experiments = db.relationship('Experiment', backref='author', lazy='dynamic')
    actions = db.relationship('Action', backref='author', lazy='dynamic')
    VNFs = db.relationship('VNF', backref='author', lazy='dynamic')

    def __repr__(self):
        return f'<User: {self.id}, Username: {self.username}, Email: {self.email}, Organization: {self.organization}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    def user_experiments(self):
        exp = Experiment.query.filter_by(user_id=self.id)
        return exp.order_by(Experiment.id.desc())

    def user_actions(self):
        acts = Action.query.filter_by(user_id=self.id).order_by(Action.id.desc()).limit(10)
        return acts

    def user_VNFs(self):
        VNFs = VNF.query.filter_by(user_id=self.id).order_by(VNF.id)
        return VNFs

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def serialization(self):
        experiment_ids = [exp.id for exp in self.user_experiments()]
        dictionary = {'Id': self.id, 'UserName': self.username, 'Email': self.email, 'Organization': self.organization,
                      'Experiments': experiment_ids}
        return dictionary


class Experiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(16))
    unattended = db.Column(db.Boolean)
    test_cases = db.Column(JSONEncodedDict)
    ues = db.Column(JSONEncodedDict)
    NSD = db.Column(db.String(256))
    slice = db.Column(db.String(64))
    executions = db.relationship('Execution', backref='experiment', lazy='dynamic')

    def __repr__(self):
        return f'<Experiment: {self.id}, Name: {self.name}, User_id: {self.user_id}, Type: {self.type}, ' \
            f'Unattended: {self.unattended}, TestCases: {self.test_cases}, NSD: {self.NSD}, Slice: {self.slice}>'

    def experiment_executions(self):
        exp = Execution.query.filter_by(experiment_id=self.id)
        return exp.order_by(Execution.id.desc())

    def serialization(self):
        execution_ids = [exe.id for exe in self.experiment_executions()]
        ueDictionary = {}
        all_UEs = HelperConfig().UEs
        if self.ues:
            for ue in self.ues:
                if ue in all_UEs.keys(): ueDictionary[ue] = all_UEs[ue]
        dictionary = {'Id': self.id, 'Name': self.name, 'User': User.query.get(self.user_id).serialization(),
                      'Executions': execution_ids, "Platform": HelperConfig().Platform,
                      "TestCases": self.test_cases, "UEs": ueDictionary, "Slice": self.slice, "NSD": self.NSD}
        return dictionary


class Execution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    start_time = db.Column(db.DATETIME)
    end_time = db.Column(db.DATETIME)
    status = db.Column(db.String(32))

    def __repr__(self):
        return f'<Execution {self.id}, Experiment_id {self.experiment_id}, Start_time {self.start_time}, ' \
            f'End_time {self.end_time}, Status {self.status}>'


class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DATETIME)
    message = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Action {self.id}, Timestamp {self.timestamp}, Message {self.message}, ' \
            f'User {self.user_id}>'


class VNF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(256))
    VNFD = db.Column(db.String(256))
    image = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<VNF {self.id}, Name {self.name}, Description {self.description}, VNFD {self.VNFD},' \
            f'Image {self.image}, User {self.user_id}>'
