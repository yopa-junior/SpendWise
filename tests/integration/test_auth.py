# tests/integration/test_auth.py

import pytest


@pytest.mark.asyncio
async def test_register_creates_unverified_user(client, devise_xaf):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "nom": "Nouvel Utilisateur",
            "email": "nouveau@example.com",
            "mot_de_passe": "MotDePasse123",
            "devise_preferee": "XAF",
            "langue_preferee": "fr",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_verified"] is False
    assert "mot_de_passe_hash" not in data  # jamais exposé


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client, devise_xaf, verified_user):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "nom": "Autre",
            "email": "test@example.com",  # déjà pris par verified_user
            "mot_de_passe": "MotDePasse123",
            "devise_preferee": "XAF",
            "langue_preferee": "fr",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client, verified_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "mot_de_passe": "Password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password_fails(client, verified_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "mot_de_passe": "MauvaisMotDePasse"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_authentication(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_token(client, auth_headers):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"