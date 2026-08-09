# tests/conftest.py

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.core.security import hash_password
from app.models.user import User, LanguePreferee
from app.models.currency import Devise

TEST_DATABASE_URL = "postgresql+asyncpg://spendwise:mathis2025@localhost:5432/spendwise_test_db"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Crée un moteur neuf par test (évite la réutilisation de connexion entre boucles asyncio),
    crée toutes les tables, fournit une session, puis nettoie et dispose le moteur après chaque test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Client HTTP de test, avec la base de données remplacée par celle de test."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def devise_xaf(db_session):
    devise = Devise(code_devise="XAF", nom="Franc CFA", symbole="FCFA")
    db_session.add(devise)
    await db_session.commit()
    return devise


@pytest_asyncio.fixture
async def devise_eur(db_session):
    devise = Devise(code_devise="EUR", nom="Euro", symbole="€")
    db_session.add(devise)
    await db_session.commit()
    return devise


@pytest_asyncio.fixture
async def verified_user(db_session, devise_xaf):
    """Un utilisateur déjà vérifié, prêt à se connecter."""
    user = User(
        id=uuid.uuid4(),
        nom="Test User",
        email="test@example.com",
        mot_de_passe_hash=hash_password("Password123"),
        devise_preferee="XAF",
        langue_preferee=LanguePreferee.FR,
        is_active=True,
        is_verified=True,
        date_creation=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client, verified_user):
    """Headers d'authentification prêts à l'emploi pour un utilisateur vérifié."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "mot_de_passe": "Password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}