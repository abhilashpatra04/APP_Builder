import requests
import json
import os

API_URL = "http://localhost:8000/api"

class APIClient:
    def __init__(self):
        self.token = None
        self.user = None

    def set_token(self, token):
        self.token = token

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, email, password):
        try:
            resp = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                return data
            return None
        except:
            return None

    def register(self, email, password):
        try:
            resp = requests.post(f"{API_URL}/auth/register", json={"email": email, "password": password})
            return resp.status_code == 200
        except:
            return False

    def get_me(self):
        if not self.token: return None
        try:
            resp = requests.get(f"{API_URL}/auth/me", headers=self._get_headers())
            if resp.status_code == 200:
                self.user = resp.json()
                return self.user
            return None
        except:
            return None

    def create_project_v2(self, prompt, project_name=None):
        payload = {"prompt": prompt}
        if project_name:
            payload["project_name"] = project_name
            
        resp = requests.post(f"{API_URL}/v2/generate", json=payload, headers=self._get_headers())
        return resp.json()

    def get_projects(self):
        resp = requests.get(f"{API_URL}/v2/projects", headers=self._get_headers())
        if resp.status_code == 200:
            return resp.json().get("projects", [])
        return []

    def get_project_status(self, project_id):
        resp = requests.get(f"{API_URL}/v2/projects/{project_id}", headers=self._get_headers())
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_plan(self, project_id):
        resp = requests.get(f"{API_URL}/v2/projects/{project_id}/plan", headers=self._get_headers())
        return resp.json() if resp.status_code == 200 else None

    def approve_plan(self, project_id):
        resp = requests.post(f"{API_URL}/v2/projects/{project_id}/approve-plan", headers=self._get_headers())
        return resp.json()

    def get_tasks(self, project_id):
        resp = requests.get(f"{API_URL}/v2/projects/{project_id}/tasks", headers=self._get_headers())
        return resp.json() if resp.status_code == 200 else None

    def approve_tasks(self, project_id):
        resp = requests.post(f"{API_URL}/v2/projects/{project_id}/approve-tasks", headers=self._get_headers())
        return resp.json()

    def get_files(self, project_id):
        resp = requests.get(f"{API_URL}/v2/projects/{project_id}/files", headers=self._get_headers())
        return resp.json().get("files", []) if resp.status_code == 200 else []

    def get_file_content(self, project_id, filepath):
        resp = requests.get(f"{API_URL}/v2/projects/{project_id}/files/{filepath}", headers=self._get_headers())
        return resp.text if resp.status_code == 200 else ""
        
    def chat_edit(self, project_id, message):
        resp = requests.post(f"{API_URL}/projects/{project_id}/chat", json={"message": message}, headers=self._get_headers())
        return resp.json() if resp.status_code == 200 else None
