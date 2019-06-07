import jwt
import json
from typing import Dict, List
from time import time
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.types import TypeDecorator, VARCHAR
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
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
        return f'<Id: {self.id}, Username: {self.username}, Email: {self.email}, Organization: {self.organization}'

    def setPassword(self, password):
        self.password_hash = generate_password_hash(password)

    def checkPassword(self, password):
        return check_password_hash(self.password_hash, password)

    def getResetPasswordToken(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    def userExperiments(self) -> List:
        exp: List = Experiment.query.filter_by(user_id=self.id)
        return exp.order_by(Experiment.id.desc())

    def userActions(self) -> List:
        acts: List = Action.query.filter_by(user_id=self.id).order_by(Action.id.desc()).limit(10)
        return acts

    def userVNFs(self) -> List:
        VNFs: List = VNF.query.filter_by(user_id=self.id).order_by(VNF.id)
        return VNFs

    @staticmethod
    def verifyResetPasswordToken(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def serialization(self) -> Dict[str, object]:
        experimentIds: List[int] = [exp.id for exp in self.userExperiments()]
        dictionary = {'Id': self.id, 'UserName': self.username, 'Email': self.email, 'Organization': self.organization,
                      'Experiments': experimentIds}
        return dictionary


@login.user_loader
def load_user(id: int) -> User:
    return User.query.get(int(id))


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
    vnflocations = db.relationship('VNFLocation', backref='experiment', lazy='dynamic')
    executions = db.relationship('Execution', backref='experiment', lazy='dynamic')

    def __repr__(self):
        return f'<Id: {self.id}, Name: {self.name}, User_id: {self.user_id}, Type: {self.type}, ' \
            f'Unattended: {self.unattended}, TestCases: {self.test_cases}, NSD: {self.NSD}, Slice: {self.slice}>'

    def experimentExecutions(self) -> List:
        exp: List = Execution.query.filter_by(experiment_id=self.id)
        return exp.order_by(Execution.id.desc())

    def experimentVNFs(self) -> List:
        vnfs: List = VNFLocation.query.filter_by(experiment_id=self.id)
        return vnfs.order_by(VNFLocation.id.asc())

    def serialization(self) -> Dict[str, object]:
        ueDictionary = {}
        vnfsLocations = []
        allUEs: List = HelperConfig().UEs
        executionIds: List = [exe.id for exe in self.experimentExecutions()]

        if self.ues:
            for ue in self.ues:
                if ue in allUEs.keys(): ueDictionary[ue] = allUEs[ue]

        for vnfLoc in self.experimentVNFs():
            vnfLocation: Dict[str, object] = VNF.query.get(vnfLoc.VNF_id).serialization()
            vnfLocation['Location'] = vnfLoc.location
            vnfsLocations.append(vnfLocation)

        dictionary = {'Id': self.id, 'Name': self.name, 'User': User.query.get(self.user_id).serialization(),
                      'Executions': executionIds, "Platform": HelperConfig().Platform,
                      "TestCases": self.test_cases, "UEs": ueDictionary, "Slice": self.slice, "NSD": self.NSD,
                      "VNF_Locations": vnfsLocations}
        return dictionary


class Execution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    start_time = db.Column(db.DATETIME)
    end_time = db.Column(db.DATETIME)
    status = db.Column(db.String(32))
    dashboard_url = db.Column(db.String(64))
    percent = db.Column(db.Integer)
    message = db.Column(db.String(128))

    def __repr__(self):
        return f'<Id: {self.id}, Experiment_id: {self.experiment_id}, Start_time: {self.start_time}, ' \
            f'End_time: {self.end_time}, Status: {self.status}, Dashboard_url: {self.dashboard_url}, ' \
            f'Percent: {self.percent}. Message: {self.message} >'


class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DATETIME)
    message = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Id: {self.id}, Timestamp: {self.timestamp}, Message: {self.message}, ' \
            f'User_id: {self.user_id}>'


class VNF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(256))
    VNFD = db.Column(db.String(256))
    image = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vnf_locations = db.relationship('VNFLocation', backref='vnf_file', lazy='dynamic')

    def __repr__(self):
        return f'<VNF: {self.id}, Name: {self.name}, Description: {self.description}, VNFD: {self.VNFD},' \
            f'Image: {self.image}, User_id: {self.user_id}>'

    def serialization(self) -> Dict[str, object]:
        dictionary = {'Id': self.id, 'Name': self.name, 'Description': self.description, 'VNFD': self.VNFD,
                      "Image": self.image, "User": self.user_id}
        return dictionary


class VNFLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(32))
    VNF_id = db.Column(db.Integer, db.ForeignKey('VNF.id'))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))

    def __repr__(self):
        return f'<Id: {self.id}, VNF_id: {self.VNF_id}, Location: {self.location}, Experiment_id: {self.experiment_id}>'
