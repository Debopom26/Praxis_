from fastapi.testclient import TestClient
from praxis.db.models import RememberedLogin, User
from praxis.main import create_app
from praxis.security import hash_password
from sqlalchemy import select


def test_device_grant_tenant_revocation_and_password_change(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        login = {"username": "admin-a", "password": "test-password-only", "tenant_id": "a"}
        ordinary = client.post('/api/v1/auth/login', json=login).json()
        assert 'refresh_token' not in ordinary
        device = client.post('/api/v1/auth/login', json={**login, 'remember': True}).json()
        secret = device['refresh_token']
        with repo.sessions() as db:
            grant = db.scalar(select(RememberedLogin))
            assert grant is not None and grant.digest != secret and len(grant.digest) == 64
        body = {'refresh_token': secret, 'tenant_id': 'a'}
        refreshed = client.post('/api/v1/auth/refresh', json=body)
        assert refreshed.status_code == 200 and refreshed.json()['expires_in'] == ordinary['expires_in']
        assert client.post('/api/v1/auth/refresh', json={**body, 'tenant_id': 'b'}).status_code == 401
        with repo.sessions.begin() as db:
            db.get(User, 'admin-a').active = False
        assert client.post('/api/v1/auth/refresh', json=body).status_code == 401
        with repo.sessions.begin() as db:
            db.get(User, 'admin-a').active = True
            db.get(User, 'admin-a').password_hash = hash_password('replacement-password')
        assert client.post('/api/v1/auth/refresh', json=body).status_code == 401
        assert client.post('/api/v1/auth/logout', json=body).status_code == 200
        assert client.post('/api/v1/auth/refresh', json=body).status_code == 401


def test_existing_access_can_upgrade_and_logout_is_device_scoped(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        login = client.post('/api/v1/auth/login', json={
            'username': 'admin-a', 'password': 'test-password-only', 'tenant_id': 'a'}).json()
        headers = {'Authorization': 'Bearer ' + login['access_token']}
        assert client.post('/api/v1/auth/remember').status_code == 401
        first = client.post('/api/v1/auth/remember', headers=headers).json()['refresh_token']
        second = client.post('/api/v1/auth/remember', headers=headers).json()['refresh_token']
        body = {'refresh_token': first, 'tenant_id': 'a'}
        assert client.post('/api/v1/auth/logout', json={**body, 'tenant_id': 'b'}).status_code == 200
        assert client.post('/api/v1/auth/refresh', json=body).status_code == 200
        client.post('/api/v1/auth/logout', json=body)
        assert client.post('/api/v1/auth/refresh', json=body).status_code == 401
        assert client.post('/api/v1/auth/refresh', json={**body, 'refresh_token': second}).status_code == 200
