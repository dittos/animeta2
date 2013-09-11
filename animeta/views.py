import flask
from animeta import models

def init_app(app):
    @app.route('/users/<username>/')
    def library(username):
        user = models.User.query.filter_by(username=username).first_or_404()
        return flask.render_template('library.html',
            user=user,
            count=user.library_items.count(),
            items=user.library_items.order_by(models.LibraryItem.updated_at.desc()),
        )
