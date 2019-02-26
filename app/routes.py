from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from REST import Dispatcher_Api
from app.models import User, Experiment
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, RunExperimentForm
from app.forms import ExperimentForm
from app.email import send_password_reset_email
import json


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = ExperimentForm()
    if form.validate_on_submit():
        experiment = Experiment(name=form.name.data, author=current_user)
        db.session.add(experiment)
        db.session.commit()
        flash('Your experiment has been created')
        return redirect(url_for('index'))
    experiments = current_user.user_experiments()
    formrun = RunExperimentForm()
    if formrun.validate_on_submit():
        try:
            api = Dispatcher_Api("127.0.0.1", "5001", "/api/v0")  # //api/v0
            jsonresponse = api.Post(formrun.id.data, formrun.exp_name.data, formrun.exp_author.data)
            flash(f'Success: {jsonresponse["Success"]} - Execution Id: '
                  f'{jsonresponse["ExecutionId"]} - Message: {jsonresponse["Message"]}')

        except Exception as e:
            flash(f'Exception while trying to connect with dispatcher: {e}')

        return redirect(url_for('index'))
    return render_template('index.html', title='Home', form=form, formRun=formrun, experiments=experiments)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You have been registered')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
