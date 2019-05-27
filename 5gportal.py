from app import create_app, db
from app.models import User, Experiment, Execution, Action, VNF
from Helper import Config
app = create_app()
config = Config()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Experiment': Experiment, 'Execution': Execution, 'Action': Action, 'VNF': VNF,
            'Config': config}
