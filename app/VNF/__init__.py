from flask import Blueprint

bp = Blueprint('VNF', __name__)

from app.VNF import routes