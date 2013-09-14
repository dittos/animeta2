# -*- coding: utf-8 -*-
import datetime
import pytz
from django.conf import settings; settings.configure(); del settings
from django.contrib.auth.hashers import check_password
from sqlalchemy.ext.associationproxy import association_proxy
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
    canonical_title = db.Column('title', db.Unicode(100), nullable=False, index=True)

    title_mappings = db.relationship('TitleMapping', backref=db.backref('work'))
    titles = association_proxy('title_mappings', 'title')

class TitleMapping(db.Model):
    __tablename__ = 'work_titlemapping'
    id = db.Column(db.Integer, primary_key=True)
    work_id = db.Column(db.Integer, db.ForeignKey(Work.id), nullable=False)
    title = db.Column(db.Unicode(100), nullable=False)
    key = db.Column(db.Unicode(100), nullable=False)

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
        ), viewonly=True, lazy='dynamic', uselist=True,
        backref=db.backref('library_item', uselist=False))

    def add_update(self, update):
        update.user = self.user
        update.work = self.work

        # Update denormalized columns
        self.progress = update.progress
        self.updated_at = update.updated_at

    def remove_update(self, update):
        last_update = (self.updates.filter(Update.id != update.id)
                           .order_by(Update.id.desc()).first())
        if last_update:
            self.progress = last_update.progress
        else:
            self.progress = ''
