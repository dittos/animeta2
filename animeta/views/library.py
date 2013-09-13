import flask
from flask.ext.login import current_user, login_required
from animeta import db, models

bp = flask.Blueprint('library', __name__)

@bp.route('/users/<username>/')
def index(username):
    user = models.User.query.filter_by(username=username).first_or_404()
    return flask.render_template('library/index.html',
        user=user,
        count=user.library_items.count(),
        items=user.library_items.order_by(models.LibraryItem.updated_at.desc()),
    )

@bp.route('/records/<id>/')
def item_detail(id):
    item = models.LibraryItem.query.get_or_404(id)
    return flask.render_template('library/item_detail.html',
        user=item.user,
        item=item,
        updates=item.updates.order_by(models.Update.id.desc()),
    )

@bp.route('/records/<id>/', methods=['POST'])
@login_required
def update_item(id):
    item = models.LibraryItem.query.get_or_404(id)
    if item.user != current_user:
        flask.abort(403)
    item.status = flask.request.form['status']
    db.session.commit()
    return flask.redirect(flask.url_for('.item_detail', id=item.id))

@bp.route('/records/<id>/updates', methods=['POST'])
@login_required
def create_update(id):
    item = models.LibraryItem.query.get_or_404(id)
    if item.user != current_user:
        flask.abort(403)
    update = models.Update(
        progress=flask.request.form['progress'],
        comment=flask.request.form['comment'],
    )
    item.updates.append(update)
    db.session.commit()
    return flask.redirect(flask.url_for('.item_detail', id=item.id))
