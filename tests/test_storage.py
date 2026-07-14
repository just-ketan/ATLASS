import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlasse.platform.storage import ObjectStorage


class TestObjectStorage(unittest.TestCase):

    def test_put_bytes_and_resolve_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ObjectStorage(base_dir=tmpdir)

            stored_path = storage.put_bytes("user/paper.pdf", b"pdf")

            self.assertTrue(stored_path.startswith(tmpdir))
            self.assertEqual(storage.get_file_path("user/paper.pdf"), stored_path)
            with open(stored_path, "rb") as f:
                self.assertEqual(f.read(), b"pdf")

    def test_object_keys_cannot_escape_storage_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ObjectStorage(base_dir=tmpdir)

            with self.assertRaises(ValueError):
                storage.put_bytes("../paper.pdf", b"pdf")


if __name__ == "__main__":
    unittest.main()
