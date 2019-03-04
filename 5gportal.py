from app import app, db
from app.models import User, Experiment, Execution


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Experiment': Experiment, 'Execution': Execution}
