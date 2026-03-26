def test_create_project(client, test_db, test_user):
    response = client.post(
        "/api/projects",
        json={
            "title": "Test Video",
            "type": "shorts",
            "topic": "5 surprising facts about coffee",
            "pipeline_config": {
                "script": True,
                "tts": True,
                "images": True,
                "video": True,
                "subtitle": True,
                "metadata": True,
            },
        },
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Video"
    assert data["type"] == "shorts"
    assert data["status"] == "draft"
    assert data["pipeline_config"]["script"] is True


def test_create_project_invalid_type(client, test_db, test_user):
    response = client.post(
        "/api/projects",
        json={
            "title": "Bad",
            "type": "invalid",
            "topic": "test",
            "pipeline_config": {"video": True},
        },
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 400
    assert "지원하지 않는 영상 유형" in response.json()["detail"]


def test_list_projects(client, test_db, test_user, test_project):
    response = client.get(
        "/api/projects",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Video"


def test_list_projects_empty(client, test_db, test_user):
    response = client.get(
        "/api/projects",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_project(client, test_db, test_user, test_project):
    response = client.get(
        f"/api/projects/{test_project.id}",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_project.id
    assert data["topic"] == "coffee facts"


def test_get_project_not_found(client, test_db, test_user):
    response = client.get(
        "/api/projects/99999",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 404


def test_delete_project(client, test_db, test_user, test_project):
    response = client.delete(
        f"/api/projects/{test_project.id}",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 204

    list_response = client.get(
        "/api/projects",
        headers={"X-User-Id": test_user.id},
    )
    assert list_response.json() == []


def test_delete_project_not_found(client, test_db, test_user):
    response = client.delete(
        "/api/projects/99999",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 404
