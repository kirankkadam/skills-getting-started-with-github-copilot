"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a known state before each test"""
    # Store original state
    original_activities = {
        "Basketball": {
            "description": "Team basketball practice and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Soccer": {
            "description": "Outdoor soccer matches and training",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 22,
            "participants": ["sarah@mergington.edu", "james@mergington.edu"]
        },
    }
    
    # Reset to original state
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Basketball" in data
        assert "Soccer" in data
        assert data["Basketball"]["max_participants"] == 15
    
    def test_activities_have_participants(self, client):
        """Test that activities include participant lists"""
        response = client.get("/activities")
        data = response.json()
        assert "participants" in data["Basketball"]
        assert "alex@mergington.edu" in data["Basketball"]["participants"]


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Basketball"]["participants"]
    
    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signups are rejected"""
        # First signup
        response1 = client.post(
            "/activities/Basketball/signup?email=alex@mergington.edu"
        )
        assert response1.status_code == 400
        assert "already signed up" in response1.json()["detail"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/NonExistent/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregister:
    """Test the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        response = client.delete(
            "/activities/Basketball/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "alex@mergington.edu" not in activities_data["Basketball"]["participants"]
    
    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant who isn't signed up"""
        response = client.delete(
            "/activities/Basketball/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from activity that doesn't exist"""
        response = client.delete(
            "/activities/NonExistent/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
