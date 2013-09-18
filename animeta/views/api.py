# -*- coding: utf-8 -*-
import functools
import flask
from flask.ext.login import current_user, login_required
from animeta import db, models, serializer

bp = flask.Blueprint('api', __name__)

def api_response(**options):
    def decorate(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            rv = flask.make_response(serializer.serialize(f(*args, **kwargs), **options))
            rv.mimetype = 'application/json'
            return rv
        return wrapped
    return decorate

@bp.route('/users/<username>')
@api_response(include_fields=['items'])
def user(username):
    return models.User.query.filter_by(username=username).first_or_404()

@bp.route('/items/<id>')
@api_response(include_fields=['updates'])
def item(id):
    return models.LibraryItem.query.get_or_404(id)

@bp.route('/items/<id>', methods=['PUT'])
@login_required
@api_response()
def update_item(id):
    item = models.LibraryItem.query.get_or_404(id)
    if item.user != current_user:
        flask.abort(403)
    item.status = flask.request.form['status']
    db.session.commit()
    return item

@bp.route('/updates', methods=['POST'])
@login_required
@api_response()
def create_update():
    id = flask.request.json['item_id']
    item = models.LibraryItem.query.get_or_404(id)
    if item.user != current_user:
        flask.abort(403)
    update = models.Update(
        progress=flask.request.json.get('progress', ''),
        comment=flask.request.json.get('comment', ''),
    )
    item.add_update(update)
    db.session.commit()
    return update

@bp.route('/updates/<id>', methods=['DELETE'])
@login_required
@api_response()
def delete_update(id):
    update = models.Update.query.get_or_404(id)
    if update.user != current_user:
        flask.abort(403)
    item = update.library_item
    item.remove_update(update)
    db.session.delete(update)
    db.session.commit()
    return item #XXX
