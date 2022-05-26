from sqlalchemy.ext.hybrid import hybrid_property

from api.extensions import db, pwd_context


class User(db.Model):
    """Basic user model"""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    _password = db.Column("password", db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = pwd_context.hash(value)

    def __repr__(self):
        return "<User %s>" % self.email

class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20))
    playlist = db.Column(db.String(20))
    thumbnail_image_url = db.Column(db.String(255))
    audio_url = db.Column(db.String(20))
    misc = db.Column(db.PickleType, default=dict())
    setter_id = db.Column(db.Integer)

    def __repr__(self):
        return 'Id: {}, Title: {}'.format(self.id, self.title)