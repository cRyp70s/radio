import pytest
from flask import url_for

from api.models import User

email = "test@test.com"

@pytest.fixture
def user(client, db):
    user_url = url_for('api.users')
    resp = client.post(user_url, json={
        "email": email,
        "password": "pasword"
    })
    yield resp
    user = User.query.filter_by(email=email).first()
    if user:
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

def test_create_user(client, user):
    assert user.status_code == 201
    assert user.get_json()["user"]["email"] == email

def test_get_user(client, admin_user, admin_headers):
    uid = admin_user.id
    user_url = url_for('api.users', user_id = uid)
    resp = client.get(user_url, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["user"]["id"] == uid

def test_get_user_admin(client, admin_user, admin_headers, user):
    uid = user.get_json()["user"]["id"]
    user_url = url_for('api.users', user_id = uid)
    resp = client.get(user_url, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["user"]["id"] == uid

def test_delete_user(client, admin_user, admin_headers, user):
    uid = user.get_json()["user"]["id"]
    user_url = url_for('api.users', user_id = uid)
    resp = client.delete(user_url, headers=admin_headers)
    assert resp.status_code == 200

    # Check that user no longer exists
    u = User.query.get(uid)
    assert u == None
