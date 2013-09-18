# -*- coding: utf-8 -*-
import flask
from animeta import models, serializer

bp = flask.Blueprint('library', __name__)

@bp.app_template_filter()
def serialize(obj, **kwargs):
    return flask.Markup(serializer.serialize(obj, **kwargs))

@bp.route('/users/<username>/')
@bp.route('/users/<username>/<path:path>')
def index(username, path=None):
    user = models.User.query.filter_by(username=username).first_or_404()
    return flask.render_template('library/index.html', user=user)
