# from fastapi import status


# class TestAuth:
#   def test_register_success(self, client):
#     response = client.post(
#       "/auth/register",
#       json={
#         "email": "mewuser@example.com",
#         "password": "securepass123"
#       }
#     )
    
#     assert response.status_code == status.HTTP_201_CREATED
#     data = response.json()
#     assert data["email"] == "newuser@example.com"
#     assert "id" in data
#     assert "created_at" in data
#     assert "hashed_password" not in data
  
#   def test_register_duplicate_email(self, client, db_session):
#     from tests.conftest import create_test_user
    
#     create_test_user(db_session, email="existing@example.com")
    
#     response = client.post(
#       "/auth/register",
#       json={
#         "email": "mewuser@example.com",
#         "password": "securepass123"
#       }
#     )
    
#     assert response.status_code == status.HTTP_400_BAD_REQUEST
#     assert response.json()["detail"] == "Email уже зарегистрирован"
  
#   def test_register_invalid_email(self, client):
#     response = client.post(
#       "/auth/register",
#       json={
#         "email": "not-an-email",
#         "password": "securepass123"
#       }
#     )
    
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
  
#   def test_register_short_password(self, client):
#     response = client.post(
#       "/auth/register",
#       json={
#         "email": "test@example.com",
#         "password": "short"
#       }
#     )
    
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
  
#   def test_login_success(self, client, db_session):
#     from tests.conftest import create_test_user
    
#     create_test_user(db_session, email="login@example.com", password="testpass123")
    
#     response = client.post(
#       "/auth/login",
#       data={
#         "email": "login@example.com",
#         "password": "testpass123"
#       }
#     )
    
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert "access_token" in data
#     assert data["token_type"] == "bearer"
  
#   def test_login_wrong_password(self, client, db_session):
#     from tests.conftest import create_test_user
    
#     create_test_user(db_session, email="login@example.com", password="testpass123")
    
#     response = client.post(
#       "/auth/login",
#       data={
#         "email": "login@example.com",
#         "password": "wrongpassword"
#       }
#     )
    
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
  
#   def test_login_nonexistent_user(self, client):
#     response = client.post(
#       "/auth/login",
#       data={
#         "username": "nonexistent@example.com",
#         "password": "testpass123"
#       }
#     )
    
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED


