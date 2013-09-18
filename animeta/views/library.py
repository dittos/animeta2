# -*- coding: utf-8 -*-
import datetime
import itertools
import flask
from flask.ext.login import current_user, login_required
from animeta import db, models, serializer

bp = flask.Blueprint('library', __name__)

@bp.app_template_filter()
def serialize(obj):
    return flask.Markup(serializer.serialize(obj))

def serialize_response(obj):
    rv = flask.make_response(serializer.serialize(obj))
    rv.mimetype = 'application/json'
    return rv

@bp.route('/users/<username>/')
def index(username):
    user = models.User.query.filter_by(username=username).first_or_404()
    items = user.library_items.order_by(models.LibraryItem.updated_at.desc().nullslast())
    return flask.render_template('library/index.html',
        user=user,
        items=items,
    )

@bp.route('/items/<id>/updates')
def item_detail(id):
    item = models.LibraryItem.query.get_or_404(id)
    return serialize_response(item.updates.order_by(models.Update.id.desc()))

@bp.route('/items/<id>', methods=['POST'])
@login_required
def update_item(id):
    item = models.LibraryItem.query.get_or_404(id)
    if item.user != current_user:
        flask.abort(403)
    item.status = flask.request.form['status']
    db.session.commit()
    return flask.jsonify(ok=True)

@bp.route('/items/<id>/updates', methods=['POST'])
@login_required
def create_update(id):
    item = models.LibraryItem.query.get_or_404(id)
    if item.user != current_user:
        flask.abort(403)
    update = models.Update(
        progress=flask.request.form['progress'],
        comment=flask.request.form['comment'],
    )
    item.add_update(update)
    db.session.commit()
    return serialize_response(update)

@bp.route('/updates/<id>', methods=['DELETE'])
@bp.route('/updates/<id>/delete', methods=['POST'])
@login_required
def delete_update(id):
    update = models.Update.query.get_or_404(id)
    if update.user != current_user:
        flask.abort(403)
    item = update.library_item
    item.remove_update(update)
    db.session.delete(update)
    db.session.commit()
    return flask.jsonify(ok=True)
