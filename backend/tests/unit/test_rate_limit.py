from app.rate_limit import SlidingWindowLimiter


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_allows_limit_then_rejects_then_recovers():
    clock = Clock()
    lim = SlidingWindowLimiter(window_s=3600, clock=clock)
    assert all(lim.hit("1.1.1.1", limit=30) is None for _ in range(30))
    retry = lim.hit("1.1.1.1", limit=30)
    assert retry is not None and 0 < retry <= 3600
    clock.now += 3600
    assert lim.hit("1.1.1.1", limit=30) is None


def test_rejected_hits_do_not_extend_the_window():
    clock = Clock()
    lim = SlidingWindowLimiter(window_s=60, clock=clock)
    lim.hit("ip", limit=1)
    clock.now += 30
    assert lim.hit("ip", limit=1) == 30
    clock.now += 30
    assert lim.hit("ip", limit=1) is None


def test_keys_are_independent_and_reset():
    lim = SlidingWindowLimiter(window_s=3600, clock=Clock())
    assert lim.hit("a", limit=1) is None
    assert lim.hit("a", limit=1) is not None
    assert lim.hit("b", limit=1) is None
    lim.reset()
    assert lim.hit("a", limit=1) is None
