import os
os.environ["PYTEST_RUNNING"] = "true"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import link, user
from app.services.auth import get_password_hash
from app.models.user import User


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
  SQLALCHEMY_TEST_DATABASE_URL,
  connect_args={"check_same_thread": False},
  poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
  autocommit=False,
  autoflush=False,
  bind=engine
)


def setup_test_db():
  Base.metadata.create_all(bind=engine)

def teardown_test_db():
  Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
  setup_test_db()
  
  db = TestingSessionLocal()
  try:
    yield db
  finally:
    db.close()
  
  teardown_test_db()


@pytest.fixture(scope="function")
def client(db_session):
  def override_get_db():
    try:
      yield db_session
    finally:
      pass
  
  app.dependency_overrides[get_db] = override_get_db
  
  app.state.limiter = None
  
  yield TestClient(app)
  
  app.dependency_overrides.clear()


def create_test_user(db, email="test@example.com", password="testpass123"):
  hashed_password = get_password_hash(password)
  user = User(email=email, hashed_password=hashed_password)
  
  db.add(user)
  db.commit()
  db.refresh(user)
  
  return user


def get_auth_token(client, email="test@example.com", password="testpass123"):
  response = client.post(
    "/auth/login",
    data={"username": email, "password": password}
  )
  return response.json()["access_token"]


