# tests/integration/test_expenses.py

import pytest



@pytest.fixture
def category_alimentation_data():
    return {"nom": "Alimentation", "icone": "restaurant", "couleur": "#f59e0b"}


async def _create_category(client, auth_headers, data):
    response = await client.post("/api/v1/categories", json=data, headers=auth_headers)
    return response.json()["id"]


async def _create_wallet(client, auth_headers, solde=100000, devise="XAF"):
    response = await client.post(
        "/api/v1/wallets",
        json={"nom_wallet": "Compte principal", "type_wallet": "banque", "solde_initial": solde, "devise": devise},
        headers=auth_headers,
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_expense_same_currency_debits_wallet_exactly(
    client, verified_user, auth_headers, devise_xaf, category_alimentation_data
):
    wallet_id = await _create_wallet(client, auth_headers)
    category_id = await _create_category(client, auth_headers, category_alimentation_data)

    expense_response = await client.post(
        "/api/v1/expenses",
        json={
            "wallet_id": wallet_id,
            "category_id": category_id,
            "montant": 5000,
            "devise": "XAF",
            "description": "Courses",
            "date_depense": "2026-07-28",
            "est_recurrente": False,
        },
        headers=auth_headers,
    )
    assert expense_response.status_code == 201

    wallet_response = await client.get(f"/api/v1/wallets/{wallet_id}", headers=auth_headers)
    assert wallet_response.json()["solde"] == "95000.00"


@pytest.mark.asyncio
async def test_delete_expense_refunds_wallet(
    client, verified_user, auth_headers, devise_xaf, category_alimentation_data
):
    wallet_id = await _create_wallet(client, auth_headers)
    category_id = await _create_category(client, auth_headers, category_alimentation_data)

    expense_response = await client.post(
        "/api/v1/expenses",
        json={
            "wallet_id": wallet_id,
            "category_id": category_id,
            "montant": 5000,
            "devise": "XAF",
            "description": "Courses",
            "date_depense": "2026-07-28",
            "est_recurrente": False,
        },
        headers=auth_headers,
    )
    expense_id = expense_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/expenses/{expense_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    wallet_response = await client.get(f"/api/v1/wallets/{wallet_id}", headers=auth_headers)
    assert wallet_response.json()["solde"] == "100000.00"  # remboursé intégralement


@pytest.mark.asyncio
async def test_expense_insufficient_balance_fails(
    client, verified_user, auth_headers, devise_xaf, category_alimentation_data
):
    wallet_id = await _create_wallet(client, auth_headers, solde=1000)
    category_id = await _create_category(client, auth_headers, category_alimentation_data)

    response = await client.post(
        "/api/v1/expenses",
        json={
            "wallet_id": wallet_id,
            "category_id": category_id,
            "montant": 5000,
            "devise": "XAF",
            "description": "Trop cher",
            "date_depense": "2026-07-28",
            "est_recurrente": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cannot_delete_category_with_expenses(
    client, verified_user, auth_headers, devise_xaf, category_alimentation_data
):
    wallet_id = await _create_wallet(client, auth_headers)
    category_id = await _create_category(client, auth_headers, category_alimentation_data)

    await client.post(
        "/api/v1/expenses",
        json={
            "wallet_id": wallet_id,
            "category_id": category_id,
            "montant": 1000,
            "devise": "XAF",
            "description": "Test",
            "date_depense": "2026-07-28",
            "est_recurrente": False,
        },
        headers=auth_headers,
    )

    delete_response = await client.delete(f"/api/v1/categories/{category_id}", headers=auth_headers)
    assert delete_response.status_code == 409