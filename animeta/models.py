# -*- coding: utf-8 -*-
import datetime
import pytz
from django.conf import settings; settings.configure(); del settings
from django.contrib.auth.hashers import check_password
from sqlalchemy import event
from flask.ext.login import UserMixin
from animeta import db

class User(UserMixin, db.Model):
    __tablename__ = 'auth_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(30), nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def check_password(self, password):
        return check_password(password, self.password)

class Work(db.Model):
    __tablename__ = 'work_work'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(100), nullable=False, index=True)

class StatusType(db.TypeDecorator):
    impl = db.Integer

    NONE = ''
    FINISHED = 'finished'
    WATCHING = 'watching'
    SUSPENDED = 'suspended'
    INTERESTED = 'interested'
    table = (FINISHED, WATCHING, SUSPENDED, INTERESTED)

    def process_bind_param(self, value, dialect):
        if value == self.NONE:
            return -1
        return self.table.index(value)

    def process_result_value(self, value, dialect):
        if value == -1:
            return self.NONE
        return self.table[value]

class Update(db.Model):
    __tablename__ = 'record_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey(Work.id), nullable=False)
    progress = db.Column('status', db.Unicode(30))
    updated_at = db.Column(db.DateTime(timezone=True))
    comment = db.Column(db.UnicodeText, nullable=False)

    user = db.relationship(User, backref=db.backref('updates', lazy='dynamic'))
    work = db.relationship(Work, backref=db.backref('updates', lazy='dynamic'))

    def __init__(self, **kwargs):
        self.updated_at = datetime.datetime.now(pytz.utc)
        super(Update, self).__init__(**kwargs)

    # Status column in an Update is not used anymore. Read-only.
    _status = db.Column('status_type', StatusType, nullable=False, default=StatusType.NONE)

    @property
    def status(self):
        return self._status

class LibraryItem(db.Model):
    __tablename__ = 'record_record'
    __table_args__ = (db.UniqueConstraint('user_id', 'work_id'), )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey(Work.id), nullable=False)
    title = db.Column(db.Unicode(100), nullable=False)
    status = db.Column('status_type', StatusType, nullable=False, default=StatusType.WATCHING)

    # Denormalized columns
    progress = db.Column('status', db.Unicode(30))
    updated_at = db.Column(db.DateTime(timezone=True))

    user = db.relationship(User, backref=db.backref('library_items', lazy='dynamic'))
    work = db.relationship(Work, backref=db.backref('library_items', lazy='dynamic'))
    updates = db.relationship(Update, primaryjoin=db.and_(
        Update.user_id == db.foreign(user_id),
        Update.work_id == db.foreign(work_id)
    ), lazy='dynamic', uselist=True, backref=db.backref('library_item', uselist=False))

@event.listens_for(LibraryItem.updates, 'append')
def append_update(item, update, initiator):
    # Update denormalized columns
    item.progress = update.progress
    item.updated_at = update.updated_at

    # Assign relationship
    update.user_id = item.user_id
    update.work_id = item.work_id

@event.listens_for(LibraryItem.updates, 'remove')
def remove_update(item, update, initiator):
    last_updates = item.updates.order_by(Update.id.desc())[:2]
    if len(last_updates) < 2:
        item.progress = ''
    else:
        item.progress = last_updates[1].progress
