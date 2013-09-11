from animeta import db

class User(db.Model):
    __tablename__ = 'auth_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(30), nullable=False)

class Work(db.Model):
    __tablename__ = 'work_work'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(100), nullable=False, index=True)

class LibraryItem(db.Model):
    STATUS_FINISHED = 0
    STATUS_WATCHING = 1
    STATUS_SUSPENDED = 2
    STATUS_INTERESTED = 3

    __tablename__ = 'record_record'
    __table_args__ = (db.UniqueConstraint('user_id', 'work_id'), )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey(Work.id), nullable=False)
    title = db.Column(db.Unicode(100), nullable=False)
    progress = db.Column('status', db.Unicode(30))
    status = db.Column('status_type', db.Integer, nullable=False, default=STATUS_WATCHING)
    updated_at = db.Column(db.DateTime(timezone=True))

    user = db.relationship(User, backref=db.backref('library_items', lazy='dynamic'))
    work = db.relationship(Work, backref=db.backref('library_items', lazy='dynamic'))

class Update(db.Model):
    __tablename__ = 'record_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    work_id = db.Column(db.Integer, db.ForeignKey(Work.id), nullable=False)
    progress = db.Column('status', db.Unicode(30))
    status = db.Column('status_type', db.Integer, nullable=False,
                        default=LibraryItem.STATUS_WATCHING)
    updated_at = db.Column(db.DateTime(timezone=True))
    comment = db.Column(db.UnicodeText, nullable=False)

    user = db.relationship(User, backref=db.backref('updates', lazy='dynamic'))
    work = db.relationship(Work, backref=db.backref('updates', lazy='dynamic'))
    library_item = db.relationship(LibraryItem, primaryjoin=db.and_(
        LibraryItem.user_id == db.foreign(user_id),
        LibraryItem.work_id == db.foreign(work_id)
    ), backref=db.backref('updates', lazy='dynamic'))
