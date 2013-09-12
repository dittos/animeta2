import flask
from animeta import models

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
