import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlasse.platform.api import create_app


class TestPlatformAPI(unittest.TestCase):

    def test_app_contract_exposes_phase_one_routes(self):
        app = create_app()
        paths = {route.path for route in app.routes}

        self.assertIn("/health", paths)
        self.assertIn("/auth/oauth", paths)
        self.assertIn("/users/{user_id}/dashboard", paths)
        self.assertIn("/users/{user_id}/papers", paths)
        self.assertIn("/users/{user_id}/projects", paths)
        self.assertIn("/users/{user_id}/notes", paths)
        self.assertIn("/users/{user_id}/conversations", paths)
        self.assertIn("/users/{user_id}/conversations/{conversation_id}/messages", paths)


if __name__ == "__main__":
    unittest.main()
