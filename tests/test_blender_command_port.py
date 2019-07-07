from unittest import TestCase

from tempfile import NamedTemporaryFile

from execute_file_in_blender import send_command, execute_file


class TestCommandPort(TestCase):
    """
    Some general tests.
    Port need to be opened in Blender with port 5000 on localhost and "Share environment" set to True.
    """
    def test_send_command(self):
        result = send_command("""print("TEST PASSED")""", port=5000)
        self.assertTrue("TEST PASSED" in result)

        for i in range(30):
            send_command("""print("test passed")""", port=5000)
        result = send_command("""print("TEST PASSED")""", port=5000)
        self.assertTrue("TEST PASSED" in result)

    def test_execute_file(self):
        with NamedTemporaryFile(mode="w", suffix='.py', delete=True) as f:
            f.write("""print("TEST PASSED")""")
            f.flush()
            result = execute_file(f.name, port=5000)
        self.assertTrue("TEST PASSED" in result)

    def test_shared_environment(self):
        send_command("""import subprocess""", port=5000)
        result = send_command(
            """try:\n    subprocess\n    print("TEST PASSED")\nexcept NameError:\n    print("TEST FAILED")""",
            port=5000)
        self.assertTrue("TEST PASSED" in result)
