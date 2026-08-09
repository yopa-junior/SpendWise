# tests/integration/test_wallets.py

import pytest


@pytest.mark.asyncio
async def test_create_wallet(client, verified_user, auth_headers):
    response = await client.post(
        "/api/v1/wallets",
        json={
            "nom_wallet": "Espèces",
            "type_wallet": "especes",
            "solde_initial": 50000,
            "devise": "XAF",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["solde"] == "50000.00"


@pytest.mark.asyncio
async def test_deposit_increases_balance(client, verified_user, auth_headers):
    create_response = await client.post(
        "/api/v1/wallets",
        json={"nom_wallet": "Espèces", "type_wallet": "especes", "solde_initial": 10000, "devise": "XAF"},
        headers=auth_headers,
    )
    wallet_id = create_response.json()["id"]

    deposit_response = await client.post(
        f"/api/v1/wallets/{wallet_id}/deposit",
        json={"montant": 5000, "reference": "Test dépôt"},
        headers=auth_headers,
    )
    assert deposit_response.status_code == 200
    assert deposit_response.json()["solde"] == "15000.00"


@pytest.mark.asyncio
async def test_withdraw_insufficient_balance_fails(client, verified_user, auth_headers):
    create_response = await client.post(
        "/api/v1/wallets",
        json={"nom_wallet": "Espèces", "type_wallet": "especes", "solde_initial": 1000, "devise": "XAF"},
        headers=auth_headers,
    )
    wallet_id = create_response.json()["id"]

    withdraw_response = await client.post(
        f"/api/v1/wallets/{wallet_id}/withdraw",
        json={"montant": 5000, "reference": "Test retrait trop élevé"},
        headers=auth_headers,
    )
    assert withdraw_response.status_code == 400


@pytest.mark.asyncio
async def test_cannot_access_other_users_wallet(client, verified_user, auth_headers, db_session, devise_xaf):
    """Vérifie qu'un utilisateur ne peut pas accéder au wallet d'un autre utilisateur."""
    import uuid
    from datetime import datetime, timezone
    from app.core.security import hash_password
    from app.models.user import User, LanguePreferee

    other_user = User(
        id=uuid.uuid4(),
        nom="Autre Utilisateur",
        email="autre@example.com",
        mot_de_passe_hash=hash_password("Password123"),
        devise_preferee="XAF",
        langue_preferee=LanguePreferee.FR,
        is_active=True,
        is_verified=True,
        date_creation=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(other_user)
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "autre@example.com", "mot_de_passe": "Password123"},
    )
    other_token = login_response.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    create_response = await client.post(
        "/api/v1/wallets",
        json={"nom_wallet": "Espèces", "type_wallet": "especes", "solde_initial": 1000, "devise": "XAF"},
        headers=auth_headers,  # créé par verified_user
    )
    wallet_id = create_response.json()["id"]

    access_response = await client.get(f"/api/v1/wallets/{wallet_id}", headers=other_headers)
    assert access_response.status_code == 404  # jamais 403, pour ne pas révéler l'existence