from Utils.Store import Store


def test_image_store_case():
    store = Store()
    assert store.image_store.get_state() == 'initial'
    store.image_store.dispatch({'type': 'set_image', 'image': 'test'})
    assert store.image_store.get_state() == 'test'


def main():
    test_image_store_case()


if __name__ == '__main__':
    main()
