import os
import sys
import unittest
from importlib.util import find_spec

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlasse.platform.api import create_app


@unittest.skipIf(find_spec("fastapi") is None, "FastAPI is not installed")
class TestPlatformAPI(unittest.TestCase):

    def test_app_contract_exposes_workspace_routes(self):
        app = create_app()
        paths = {route.path for route in app.routes}

        self.assertIn("/health", paths)
        self.assertIn("/auth/oauth", paths)
        self.assertIn("/users/{user_id}/dashboard", paths)
        self.assertIn("/users/{user_id}/papers", paths)
        self.assertIn("/users/{user_id}/knowledge", paths)
        self.assertIn("/users/{user_id}/papers/upload", paths)
        self.assertIn("/users/{user_id}/papers/{paper_id}/events", paths)
        self.assertIn("/users/{user_id}/papers/{paper_id}/knowledge", paths)
        self.assertIn("/users/{user_id}/papers/{paper_id}/knowledge/promote", paths)
        self.assertIn("/users/{user_id}/projects", paths)
        self.assertIn("/users/{user_id}/notes", paths)
        self.assertIn("/users/{user_id}/conversations", paths)
        self.assertIn("/users/{user_id}/conversations/{conversation_id}/messages", paths)


if __name__ == "__main__":
    unittest.main()
