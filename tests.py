import unittest

from Tests.ImageStore import TestMethods as ImageTests


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(ImageTests())
    unittest.TextTestRunner(verbosity=2).run(suite)
