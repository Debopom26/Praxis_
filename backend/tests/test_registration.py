from fastapi.testclient import TestClient
from praxis.db.models import Membership, Organization, User
from praxis.main import create_app
from sqlalchemy import select


def _login(client: TestClient, tenant: str, username: str, password: str) -> dict[str, str]:
    response = client.post('/api/v1/auth/login', json={
        'tenant_id': tenant, 'username': username, 'password': password,
    })
    assert response.status_code == 200
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


def test_register_new_organization_and_admin_create_caller(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        registration = {
            'tenant_id': 'new-org', 'organization_name': 'New Organization',
            'username': 'new-admin', 'password': 'private-test-password',
        }
        assert client.post('/api/v1/auth/register', json=registration).status_code == 201
        admin = _login(client, 'new-org', 'new-admin', registration['password'])
        assert client.get('/api/v1/dashboard/sessions', headers=admin).status_code == 200
        assert client.post('/api/v1/admin/hosts', headers=admin, json={
            'username': 'new-caller', 'password': 'another-test-password',
        }).status_code == 201
        caller = _login(client, 'new-org', 'new-caller', 'another-test-password')
        assert client.get('/api/v1/dashboard/sessions', headers=caller).status_code == 200
        assert client.post('/api/v1/admin/hosts', headers=caller, json={
            'username': 'not-allowed', 'password': 'another-test-password',
        }).status_code == 403
        with repo.sessions() as db:
            assert db.get(Organization, 'new-org').name == 'New Organization'
            assert db.scalar(select(Membership.role).join(User).where(
                User.username == 'new-admin', Membership.tenant_id == 'new-org')) == 'admin'
            assert db.scalar(select(Membership.role).join(User).where(
                User.username == 'new-caller', Membership.tenant_id == 'new-org')) == 'host'
            assert db.scalar(select(User.password_hash).where(
                User.username == 'new-caller')) != 'another-test-password'


def test_registration_conflicts_do_not_leave_partial_rows(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        payload = {'tenant_id': 'a', 'organization_name': 'Collision',
                   'username': 'fresh-one', 'password': 'private-test-password'}
        assert client.post('/api/v1/auth/register', json=payload).status_code == 409
        payload['tenant_id'] = 'fresh-org'
        payload['username'] = 'admin-a'
        assert client.post('/api/v1/auth/register', json=payload).status_code == 409
        with repo.sessions() as db:
            assert db.get(Organization, 'fresh-org') is None
            assert db.scalar(select(User.id).where(User.username == 'fresh-one')) is None
        payload['username'] = 'fresh-one'
        payload['organization_name'] = '   '
        assert client.post('/api/v1/auth/register', json=payload).status_code == 422
        payload['organization_name'] = 'Fresh Organization'
        payload['password'] = 'short'
        assert client.post('/api/v1/auth/register', json=payload).status_code == 422


def test_existing_organization_cannot_be_joined_without_admin(repo, settings):
    with TestClient(create_app(settings, repo)) as client:
        assert client.post('/api/v1/admin/hosts', json={
            'username': 'intruder', 'password': 'private-test-password',
        }).status_code == 401
        other_tenant = _login(client, 'b', 'admin-b', 'test-password-only')
        assert client.post('/api/v1/admin/hosts', headers=other_tenant, json={
            'username': 'tenant-b-user', 'password': 'private-test-password',
        }).status_code == 201
        assert client.post('/api/v1/auth/login', json={
            'tenant_id': 'a', 'username': 'tenant-b-user',
            'password': 'private-test-password',
        }).status_code == 401
