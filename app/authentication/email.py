from flask import render_template, current_app
from app.email import sendEmail
from app.models import User
from Helper import Log


def sendPasswordResetEmail(user: User):
    token = user.getResetPasswordToken()
    sendEmail('[5Genesis] Reset Your Password',
              recipients=[user.email],
              text_body=render_template('email/resetPassword.txt', user=user, token=token),
              html_body=render_template('email/resetPassword.html', user=user, token=token))
    Log.I(f'Sent password reset to {user.email}')
