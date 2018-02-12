import unittest

from Tests.Image import TestMethods as ImageTests


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(ImageTests())
    unittest.TextTestRunner(verbosity=2).run(suite)
