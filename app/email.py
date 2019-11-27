from threading import Thread
from flask import current_app
from flask_mail import Message
from app import mail


def sendAsyncEmail(app, msg):
    with app.app_context():
        mail.send(msg)


def sendEmail(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=sendAsyncEmail, args=(current_app._get_current_object(), msg)).start()
