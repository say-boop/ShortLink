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
  
  def test_link_validity_period(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    from app.models.link import Link
    from app.services.shortcode import generate_unique_short_code
    from datetime import datetime, timezone, timedelta
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")
    
    short_code = generate_unique_short_code(db_session)
    
    expired_link = Link(
      short_code=short_code,
      original_url="https://example.com",
      user_id=user.id,
      expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    )
    db_session.add(expired_link)
    db_session.commit()
    
    response = client.get(f"/links/{short_code}")
    
    assert response.status_code == status.HTTP_410_GONE
    assert response.json()["detail"] == "Срок действия ссылки истёк"
    
    db_session.refresh(expired_link)
    assert expired_link.clicks == 0
  
  def test_create_link_with_past_expires_at(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    from datetime import datetime, timezone, timedelta
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")
    
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    
    response = client.post(
      "/links/shorten",
      json={
        "original_url": "https://example.com",
        "expires_at": past_date
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
  
  def test_search_links(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")    
    
    client.post(
      "/links/shorten",
      json={
        "original_url": "https://google.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    client.post(
      "/links/shorten",
      json={
        "original_url": "https://youtube.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    response = client.get(
      "links/?search=google",
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["original_url"] == "https://google.com"
  
  def test_sort_by_clicks(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    from app.models.link import Link
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")    
    
    r1 = client.post(
      "/links/shorten",
      json={
        "original_url": "https://google.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    r2 = client.post(
      "/links/shorten",
      json={
        "original_url": "https://youtube.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    code1 = r1.json()["short_code"]
    code2 = r2.json()["short_code"]
    
    link1 = db_session.query(Link).filter(Link.short_code == code1).first()
    link1.clicks += 10
    db_session.commit()
    
    response = client.get(
      "/links/?order_by=clicks&order_dir=desc",
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["short_code"] == code1
    assert data[0]["clicks"] == 10
  
  def test_sort_by_date(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")    
    
    client.post(
      "/links/shorten",
      json={
        "original_url": "https://google.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    client.post(
      "/links/shorten",
      json={
        "original_url": "https://youtube.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    response = client.get(
      "/links/?order_by=created_at&order_dir=asc",
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["original_url"] == "https://google.com"
    assert data[1]["original_url"] == "https://youtube.com"
  
  def test_search_and_sort(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")    
    
    client.post(
      "/links/shorten",
      json={
        "original_url": "https://google.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    client.post(
      "/links/shorten",
      json={
        "original_url": "https://youtube.com/page1"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    client.post(
      "/links/shorten",
      json={
        "original_url": "https://youtube.com/page2"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    response = client.get(
      "/links/?search=google&order_by=created_at&order_dir=desc",
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    for link in data:
      assert "google" in link["original_url"]
  
  def test_pagination_with_search(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")    
    
    for i in range(5):
      client.post(
        "/links/shorten",
        json={
          "original_url": f"https://test.com/page{i}"
        },
        headers={
          "Authorization": f"Bearer {token}"
        }
      )
    
    response = client.get(
      "/links/?search=test&limit=2&skip=0",
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
  
  def test_search_no_results(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")    
    
    client.post(
      "/links/shorten",
      json={
        "original_url": "https://google.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    response = client.get(
      "/links/?search=nonexistent123456",
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0
  
  def test_patch_updating_user_link(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")
    
    response_post = client.post(
      "/links/shorten",
      json={
        "original_url": "https://old-url.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    short_code_url = response_post.json()["short_code"]
    
    response_patch = client.patch(
      f"/links/{short_code_url}",
      json={
        "original_url": "https://new-url.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response_patch.status_code == status.HTTP_200_OK
    data = response_patch.json()
    assert data["original_url"] == "https://new-url.com"
  
  def test_stats_user(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    from app.models.link import Link
    from datetime import datetime, timezone, timedelta
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")
    
    resp1 = client.post(
      "/links/shorten",
      json={
        "original_url": "https://first-url.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    resp2 = client.post(
      "/links/shorten",
      json={
        "original_url": "https://second-url.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    resp3 = client.post(
      "/links/shorten",
      json={
        "original_url": "https://third-url.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    code1 = resp1.json()["short_code"]
    code2 = resp2.json()["short_code"]
    code3 = resp3.json()["short_code"]
    
    link1 = db_session.query(Link).filter(Link.short_code == code1).first()
    link1.clicks = 25
    db_session.commit()
    
    link2 = db_session.query(Link).filter(Link.short_code == code2).first()
    link2.created_at = datetime.now(timezone.utc) - timedelta(days=2)
    link2.clicks = 15
    db_session.commit()
    
    link3 = db_session.query(Link).filter(Link.short_code == code3).first()
    link3.expires_at = datetime.now(timezone.utc) - timedelta(days=3)
    link3.clicks = 10
    db_session.commit()
    
    response_get = client.get(
      "/links/stats",
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response_get.status_code == status.HTTP_200_OK
    data = response_get.json()
    assert data["total_links"] == 3
    assert data["total_clicks"] == 50
    assert data["most_popular"]["original_url"] == "https://first-url.com"
    assert data["recently_created"]["original_url"] == "https://first-url.com"
    assert data["expired_count"] == 1
  
  def test_duplicate_url_returns_existing(self, db_session, client):
    from tests.conftest import create_test_user, get_auth_token
    
    user = create_test_user(db_session, email="testuser123@example.com", password="testuser123123")
    token = get_auth_token(client, email="testuser123@example.com", password="testuser123123")
    
    response_first = client.post(
      "/links/shorten",
      json={
        "original_url": "https://example.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    short_code_first_resp = response_first.json()["short_code"]
    
    response_second = client.post(
      "/links/shorten",
      json={
        "original_url": "https://example.com"
      },
      headers={
        "Authorization": f"Bearer {token}"
      }
    )
    
    assert response_second.status_code == status.HTTP_200_OK
    data = response_second.json()
    assert data["short_code"] == short_code_first_resp