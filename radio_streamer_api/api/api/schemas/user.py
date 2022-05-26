from api.models import User
from api.extensions import ma, db


class UserSchema(ma.SQLAlchemyAutoSchema):

    id = ma.Int(dump_only=True)
    is_admin = ma.Boolean(dump_only=True)
    email = ma.Email(required=True)
    password = ma.String(load_only=True, required=True)

    class Meta:
        model = User
        sqla_session = db.session
        load_instance = True
        exclude = ("_password",)
