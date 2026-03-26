def test_create_api_key(client, test_db, test_user):
    response = client.post(
        "/api/settings/api-keys",
        json={"provider": "openai", "key": "sk-test-key-1234567890"},
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "openai"
    assert "****" in data["masked_key"] or "..." in data["masked_key"]
    assert "key" not in data
    assert data["is_valid"] is True


def test_create_api_key_invalid_provider(client, test_db, test_user):
    response = client.post(
        "/api/settings/api-keys",
        json={"provider": "invalid_provider", "key": "sk-test"},
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 400
    assert "지원하지 않는 provider" in response.json()["detail"]


def test_create_api_key_replaces_existing(client, test_db, test_user, test_api_key):
    response = client.post(
        "/api/settings/api-keys",
        json={"provider": "openai", "key": "sk-new-key-9999"},
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 201

    list_response = client.get(
        "/api/settings/api-keys",
        headers={"X-User-Id": test_user.id},
    )
    openai_keys = [k for k in list_response.json() if k["provider"] == "openai"]
    assert len(openai_keys) == 1


def test_list_api_keys(client, test_db, test_user, test_api_key):
    response = client.get(
        "/api/settings/api-keys",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["provider"] == "openai"


def test_list_api_keys_empty(client, test_db, test_user):
    response = client.get(
        "/api/settings/api-keys",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_delete_api_key(client, test_db, test_user, test_api_key):
    response = client.delete(
        f"/api/settings/api-keys/{test_api_key.id}",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 204

    list_response = client.get(
        "/api/settings/api-keys",
        headers={"X-User-Id": test_user.id},
    )
    assert list_response.json() == []


def test_delete_api_key_not_found(client, test_db, test_user):
    response = client.delete(
        "/api/settings/api-keys/99999",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 404


def test_create_api_key_without_auth(client, test_db):
    response = client.post(
        "/api/settings/api-keys",
        json={"provider": "openai", "key": "sk-test"},
    )
    assert response.status_code == 422
