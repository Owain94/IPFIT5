from threading import Timer


def debounce(wait):
    """
    Decorator that will postpone a functions execution until after wait seconds
    have elapsed since the last time it was invoked.

    :param wait: Time te wait in seconds

    :return: Debounce decorator
    """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except AttributeError:
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator
