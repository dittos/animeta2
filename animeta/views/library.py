# -*- coding: utf-8 -*-
import datetime
import itertools
import flask
from flask.ext.login import current_user, login_required
from animeta import db, models

bp = flask.Blueprint('library', __name__)

def _date_header(date):
    # 오늘/어제/그저께/그끄저께/이번 주/지난 주/이번 달/지난 달/YYYY-MM
    today = datetime.date.today()
    dt = lambda **kwargs: today - datetime.timedelta(**kwargs)
    if date == today: return u'오늘'
    elif date == dt(days=1): return u'어제'
    elif date == dt(days=2): return u'그저께'
    elif date == dt(days=3): return u'그끄저께'
    elif date.isocalendar()[:2] == today.isocalendar()[:2]:
        return u'이번 주'
    elif date.isocalendar()[:2] == dt(weeks=1).isocalendar()[:2]:
        return u'지난 주'
    elif date.year == today.year and date.month == today.month:
        return u'이번 달'
    else:
        last_month = (today.year, today.month - 1)
        if last_month[1] == 0:
            last_month = (last_month[0] - 1, 12)
        if date.year == last_month[0] and date.month == last_month[1]:
            return u'지난 달'
        else:
            return date.strftime('%Y/%m')

def group_items(items):
    return itertools.groupby(items, lambda item: _date_header(item.updated_at))

@bp.route('/users/<username>/')
def index(username):
    user = models.User.query.filter_by(username=username).first_or_404()
    items = user.library_items.order_by(models.LibraryItem.updated_at.desc().nullslast())
    return flask.render_template('library/index.html',
        user=user,
        count=user.library_items.count(),
        item_groups=group_items(items),
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
    item.add_update(update)
    db.session.commit()
    return flask.redirect(flask.url_for('.item_detail', id=item.id))

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
    return flask.redirect(flask.url_for('.item_detail', id=item.id))
