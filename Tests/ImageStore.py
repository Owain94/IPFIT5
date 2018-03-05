import unittest

from Utils.Store.Image import ImageStore
from Utils.Store.Actions.ImageStoreActions import ImageStoreActions


class TestMethods(unittest.TestCase):
    @classmethod
    def test_image_store_case(cls):
        store = ImageStore().image_store
        assert store.get_state() == 'initial'

        store.dispatch(ImageStoreActions.set_image('test'))
        assert store.get_state() == 'test'

        store.dispatch(ImageStoreActions.reset_state())
        assert store.get_state() == 'initial'
