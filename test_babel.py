
from flask import Flask, session
from flask_babel import Babel, gettext as _
import os

app = Flask(__name__)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'app/translations'
babel = Babel(app)

@babel.localeselector
def get_locale():
    return 'pt_BR'

with app.test_request_context():
    print(f"Locale: {get_locale()}")
    print(f"Awaiting Payment: {_('Awaiting Payment')}")
    print(f"Total Clients: {_('Total Clients')}")
    print(f"DASHBOARD_AWAITING_PAYMENT: {_('DASHBOARD_AWAITING_PAYMENT')}")
    print(f"Pending Contracts: {_('Pending Contracts')}")
