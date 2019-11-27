from flask import Blueprint

bp = Blueprint('execution', __name__)

from app.execution import routes
