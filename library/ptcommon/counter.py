class Counter:
    """A simple counter class"""

    def __init__(self, max, current=0):
        self._current = current
        self._max = max

    def increment(self):
        if self._current < self._max:
            self._current += 1
            return True
        else:
            return False

    def reset(self):
        self._current = 0

    def maxed(self):
        return (self._current == self._max)
