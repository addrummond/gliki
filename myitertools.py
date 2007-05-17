def drop(n, it):
    it = iter(it)
    for i in xrange(n):
        it.next()
    return it

def first(it, otherwise=None):
    it = iter(it)
    try:
        return it.next()
    except StopIteration:
        return otherwise

