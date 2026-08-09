# tests/integration/test_budgets.py

import pytest


async def _create_category(client, auth_headers, nom="Alimentation", icone="restaurant", couleur="#f59e0b"):
    response = await client.post(
        "/api/v1/categories",
        json={"nom": nom, "icone": icone, "couleur": couleur},
        headers=auth_headers,
    )
    return response.json()["id"]


async def _create_wallet(client, auth_headers, solde=100000, devise="XAF"):
    response = await client.post(
        "/api/v1/wallets",
        json={"nom_wallet": "Compte principal", "type_wallet": "banque", "solde_initial": solde, "devise": devise},
        headers=auth_headers,
    )
    return response.json()["id"]


async def _create_expense(client, auth_headers, wallet_id, category_id, montant, date_depense="2026-07-28"):
    return await client.post(
        "/api/v1/expenses",
        json={
            "wallet_id": wallet_id,
            "category_id": category_id,
            "montant": montant,
            "devise": "XAF",
            "description": "Test",
            "date_depense": date_depense,
            "est_recurrente": False,
        },
        headers=auth_headers,
    )


@pytest.mark.asyncio
async def test_budget_progress_calculation(client, verified_user, auth_headers, devise_xaf):
    category_id = await _create_category(client, auth_headers)
    wallet_id = await _create_wallet(client, auth_headers)

    budget_response = await client.post(
        "/api/v1/budgets",
        json={
            "category_id": category_id,
            "montant_limite": 10000,
            "devise": "XAF",
            "periode": "mensuel",
            "date_debut": "2026-07-01",
        },
        headers=auth_headers,
    )
    budget_id = budget_response.json()["id"]

    await _create_expense(client, auth_headers, wallet_id, category_id, 8500)

    progress_response = await client.get(f"/api/v1/budgets/{budget_id}/progress", headers=auth_headers)
    progress = progress_response.json()

    assert progress["montant_depense"] == "8500.00"
    assert progress["seuil_80_atteint"] is True
    assert progress["seuil_100_atteint"] is False


@pytest.mark.asyncio
async def test_budget_notification_created_on_threshold(client, verified_user, auth_headers, devise_xaf):
    category_id = await _create_category(client, auth_headers)
    wallet_id = await _create_wallet(client, auth_headers)

    await client.post(
        "/api/v1/budgets",
        json={
            "category_id": category_id,
            "montant_limite": 10000,
            "devise": "XAF",
            "periode": "mensuel",
            "date_debut": "2026-07-01",
        },
        headers=auth_headers,
    )

    await _create_expense(client, auth_headers, wallet_id, category_id, 8500)

    notifications_response = await client.get("/api/v1/notifications", headers=auth_headers)
    notifications = notifications_response.json()

    seuil_80_notifs = [n for n in notifications if n["type"] == "budget_seuil_80"]
    assert len(seuil_80_notifs) == 1


@pytest.mark.asyncio
async def test_budget_notification_not_duplicated_same_period(client, verified_user, auth_headers, devise_xaf):
    """Vérifie l'anti-spam : deux dépenses qui maintiennent le même seuil ne créent qu'une seule notification."""
    category_id = await _create_category(client, auth_headers)
    wallet_id = await _create_wallet(client, auth_headers)

    await client.post(
        "/api/v1/budgets",
        json={
            "category_id": category_id,
            "montant_limite": 10000,
            "devise": "XAF",
            "periode": "mensuel",
            "date_debut": "2026-07-01",
        },
        headers=auth_headers,
    )

    await _create_expense(client, auth_headers, wallet_id, category_id, 8500)
    await _create_expense(client, auth_headers, wallet_id, category_id, 200)  # reste sous 100%, toujours >80%

    notifications_response = await client.get("/api/v1/notifications", headers=auth_headers)
    notifications = notifications_response.json()

    seuil_80_notifs = [n for n in notifications if n["type"] == "budget_seuil_80"]
    assert len(seuil_80_notifs) == 1  # jamais dupliqué