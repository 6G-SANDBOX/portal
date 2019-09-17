from flask import Blueprint

bp = Blueprint('NsManagement', __name__)

from app.ns_management import routes
