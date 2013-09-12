import flask
from flask.ext.login import LoginManager, login_user, logout_user
from animeta import app, models

bp = flask.Blueprint('auth', __name__)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(user_id)

@bp.route('/login/', methods=('GET', 'POST'))
def login():
    # TODO: error message
    # TODO: get redirect url parameter
    if flask.request.method == 'POST':
        user = models.User.query.filter_by(username=flask.request.form['username']).first()
        if user and user.check_password(flask.request.form['password']):
            login_user(user, remember=flask.request.form.get('remember') == '1')
            return flask.redirect(flask.url_for('library.index', username=user.username))
    return flask.render_template('auth/login.html')

@bp.route('/logout/')
def logout():
    logout_user()
    return flask.redirect(flask.url_for('.login'))
