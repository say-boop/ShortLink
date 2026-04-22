from fastapi import status


class TestLinks:
  def test_create_link_unauthorized(self, client):
    response = client.post(
      "/links/shorten",
      json={
        "original_url": "https://example.com"
      }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
  
  def test_create_link_success(self, client, db_session):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session)
    token = get_auth_token(client)
    
    response = client.post(
      "/links/shorten",
      json={
        "original_url": "https://example.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["original_url"] == "https://example.com"
    assert len(data["short_code"]) == 6
    assert data["clicks"] == 0
    assert data["user_id"] == user.id
  
  def test_create_link_invalid_url(self, client, db_session):
    from tests.conftest import get_auth_token, create_test_user
    
    user = create_test_user(db_session, email="invalid_url_test@example.com")
    token = get_auth_token(client, email="invalid_url_test@example.com")
    
    response = client.post(
      "/links/shorten",
      json={
        "original_url": "not-a-url"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
  
  def test_redirect_success(self, client, db_session):
    from tests.conftest import create_test_user, get_auth_token
    from app.models.link import Link
    
    user = create_test_user(db_session, email="redirect_test@example.com", password="testpass123")
    token = get_auth_token(client, email="redirect_test@example.com", password="testpass123")
    
    create_response = client.post(
      "/links/shorten",
      json={
        "original_url": "https://example.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    short_code = create_response.json()["short_code"]
    
    redirect_response = client.get(
      f"/links/{short_code}",
      follow_redirects=False
    )
    
    assert redirect_response.status_code == status.HTTP_302_FOUND
    assert redirect_response.headers["location"] == "https://example.com"
    
    link = db_session.query(Link).filter(Link.short_code == short_code).first()
    assert link.clicks == 1
  
  def test_redirect_not_found(self, client):
    response = client.get("/links/nonexistent")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Ссылка не найдена"
  
  def test_stats_success(self, client, db_session):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="stats_test@example.com", password="testpass123")
    token = get_auth_token(client, email="stats_test@example.com", password="testpass123")
    
    create_response = client.post(
      "/links/shorten",
      json={
        "original_url": "https://example.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    short_code = create_response.json()["short_code"]
    
    stats_response = client.get(f"/links/{short_code}/stats")
    
    assert stats_response.status_code == status.HTTP_200_OK
    data = stats_response.json()
    assert data["short_code"] == short_code
    assert data["original_url"] == "https://example.com"
    assert data["clicks"] == 0
    assert "id" not in data
  
  def test_stats_not_found(self, client):
    response = client.get("/links/nonexistent/stats")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Ссылка не найдена"
  
  def test_get_list_user_links(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")
    
    response = client.get(
      "/links/",
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    if isinstance(data, list):
      for i in range(len(data)):
        assert data[i]["user_id"] == user.id
  
  def test_delete_link_user(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    first_user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token_first_user = get_auth_token(client, email="testuser123@example.com", password="testuser123123")
    
    second_user = create_test_user(db_session, email="test123@example.com", password="test123123")
    token_second_user = get_auth_token(client, email="test123@example.com", password="test123123")
    
    response = client.post(
      "/links/shorten",
      json={
        "original_url": "https://example.com"
      },
      headers={
        "Authorization": f"Bearer {token_first_user}"
      }
    )
    
    data_create_url = response.json()
    short_code_url = data_create_url["short_code"]
    
    response_del_strang_url = client.delete(
      f"/links/{short_code_url}",
      headers={
        "Authorization": f"Bearer {token_second_user}"
      }
    )
    
    assert response_del_strang_url.status_code == status.HTTP_403_FORBIDDEN
    
    response_delete = client.delete(
      f"/links/{short_code_url}",
      headers={
        "Authorization": f"Bearer {token_first_user}"
      }
    )
    
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT
    
    response_get_del_url = client.get(
      f"/links/{short_code_url}",
      headers={
        "Authorization": f"Bearer {token_first_user}"
      }
    )
    
    assert response_get_del_url.status_code == status.HTTP_404_NOT_FOUND