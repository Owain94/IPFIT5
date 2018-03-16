import unittest

from Tests.ImageStore import TestMethods as ImageTests


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromModule(ImageTests()))

    unittest.TextTestRunner(verbosity=2).run(suite)
