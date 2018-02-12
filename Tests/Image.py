import unittest

from Utils.Store import Store


class TestMethods(unittest.TestCase):
    def test_image_store_case(self):
        store = Store()
        assert store.image_store.get_state() == 'initial'
        store.image_store.dispatch({'type': 'set_image', 'image': 'test'})
        assert store.image_store.get_state() == 'test'