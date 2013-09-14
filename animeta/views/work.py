import flask
from animeta import db, models

bp = flask.Blueprint('work', __name__)

@bp.route('/works/<title>/')
def index(title):
    work = models.Work.query.filter(models.Work.titles.contains(title)).first()
    return flask.render_template('work/index.html', work=work)
