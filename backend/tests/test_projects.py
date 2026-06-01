"""Integration tests for project CRUD and scope generation."""
import pytest


ADAS_PROJECT = {
    "project_id": "TEST-001",
    "name": "Test ADAS Project",
    "product_type": "ADAS ECU",
    "product_line": "ADAS",
    "phase": "Concept",
    "system_boundary": "Camera and radar perception stack",
    "selected_aspects": ["QM", "FuSA"],
}


@pytest.mark.asyncio
async def test_create_project(client):
    response = await client.post("/api/v1/projects", json=ADAS_PROJECT)
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == "TEST-001"
    assert data["product_line"] == "ADAS"
    # Default scope should be generated (may be empty if seed not run)
    assert "scope" in data
    return data


@pytest.mark.asyncio
async def test_list_projects(client):
    # Create a project first
    await client.post("/api/v1/projects", json={**ADAS_PROJECT, "project_id": "TEST-LIST-001"})
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    projects = response.json()
    assert isinstance(projects, list)
    ids = [p["project_id"] for p in projects]
    assert "TEST-LIST-001" in ids


@pytest.mark.asyncio
async def test_duplicate_project_id(client):
    payload = {**ADAS_PROJECT, "project_id": "TEST-DUP-001"}
    r1 = await client.post("/api/v1/projects", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/projects", json=payload)
    assert r2.status_code == 422
    assert "already exists" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_get_project_detail(client):
    create = await client.post(
        "/api/v1/projects", json={**ADAS_PROJECT, "project_id": "TEST-GET-001"}
    )
    assert create.status_code == 201
    project_uuid = create.json()["id"]

    response = await client.get(f"/api/v1/projects/{project_uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "TEST-GET-001"


@pytest.mark.asyncio
async def test_update_project(client):
    create = await client.post(
        "/api/v1/projects", json={**ADAS_PROJECT, "project_id": "TEST-UPD-001"}
    )
    pid = create.json()["id"]

    response = await client.put(f"/api/v1/projects/{pid}", json={"name": "Updated Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_project(client):
    create = await client.post(
        "/api/v1/projects", json={**ADAS_PROJECT, "project_id": "TEST-DEL-001"}
    )
    pid = create.json()["id"]

    del_r = await client.delete(f"/api/v1/projects/{pid}")
    assert del_r.status_code == 204

    get_r = await client.get(f"/api/v1/projects/{pid}")
    assert get_r.status_code == 404


@pytest.mark.asyncio
async def test_project_not_found(client):
    response = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
