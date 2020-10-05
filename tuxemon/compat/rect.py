def intersect(r1, r2):
    return (((r2.left <= r1.left < r2.right) or
             (r1.left <= r2.left < r1.right)) and
            ((r2.top <= r1.top < r2.bottom) or
             (r1.top <= r2.top < r1.bottom)))


class Rect:
    """
    Pure Python Rect class that follows the PyGame API

    GIANT WARNING: This is completely in python and will be much slower than
                   PyGame's built in Rect class.  This rect should be used only
                   if needed!

    These rects support floating point and are hashable.
    """

    __slots__ = ['_x', '_y', '_w', '_h']

    def __init__(self, arg):
        """
        should accept rect like object or tuple of two tuples or one tuple
        of four numbers, store :x,y,h,w
        """

        if isinstance(arg, Rect):
            self._x, self._y, self._w, self._h = arg
        elif isinstance(arg, list) or isinstance(arg, tuple):
            if len(arg) == 2:
                self._x, self._y = arg[0]
                self._w, self._h = arg[1]
            elif len(arg) == 4:
                self._x, self._y, self._w, self._h = arg
        elif hasattr(arg, 'rect'):
            self._x, self._y, self._w, self._h = arg.rect
        else:
            self._x, self._y, self._w, self._h = arg

    def __len__(self):
        return 4

    def __getitem__(self, key):
        if key == 0:
            return self._x
        elif key == 1:
            return self._y
        elif key == 2:
            return self._w
        elif key == 3:
            return self._h
        raise IndexError

    def copy(self):
        return Rect(self)

    def move(self, x, y):
        return Rect((self._x + x, self._y + y, self._w, self._h))

    def inflate(self, x, y):
        return Rect((self._x - x / 2, self._y - y / 2,
                     self._w + x, self._h + y))

    def clamp(self):
        pass

    def clip(self, other):
        raise NotImplementedError

    def union(self, other):
        return Rect((min(self._x, other.left), min(self._y, other.top),
                     max(self._w, other.right), max(self._h, other.height)))

    def unionall(self, *rects):
        rects.append(self)
        left = min([r.left for r in rects])
        top = min([r.top for r in rects])
        right = max([r.right for r in rects])
        bottom = max([r.bottom for r in rects])
        return Rect(left, top, right, bottom)

    def fit(self):
        raise NotImplementedError

    def normalize(self):
        if self._w < 0:
            self._x += self._w
            self._w = -self._x
        if self._h < 0:
            self._y += self._h
            self._h = -self._y

    def contains(self, other):
        other = Rect(other)
        return ((self._x <= other.left) and
                (self._y <= other.top) and
                (self._x + self._w >= other.right) and
                (self._y + self._h >= other.bottom) and
                (self._x + self._w > other.left) and
                (self._y + self._h > other.top))

    def collidepoint(self, point):
        x, y = point
        return self._x <= x < self._x + self._w and \
               self._y <= y < self._y + self._h

    def colliderect(self, other):
        return intersect(self, Rect(other))

    def collidelist(self, rects):
        for i, rect in enumerate(rects):
            if intersect(self, rect):
                return i
        return -1

    def collidelistall(self, l):
        return [i for i, rect in enumerate(l) if intersect(self, Rect(rect))]

    def collidedict(self):
        raise NotImplementedError

    def collidedictall(self):
        raise NotImplementedError

    @property
    def top(self):
        return self._y

    @property
    def left(self):
        return self._x

    @property
    def bottom(self):
        return self._y + self._h

    @property
    def right(self):
        return self._x + self._w

    @property
    def topleft(self):
        return self._x, self._y

    @property
    def bottomleft(self):
        return self._x, self._y + self._h

    @property
    def topright(self):
        return self._x + self._w, self._y

    @property
    def bottomright(self):
        return self._x + self._w, self._y + self._h

    @property
    def midtop(self):
        return self._x + self._w / 2, self._y

    @property
    def midleft(self):
        return self._x, self._y + self._h / 2

    @property
    def midbottom(self):
        return self._x + self._w / 2, self._y + self._h

    @property
    def midright(self):
        return self._x + self._w, self._y + self._h / 2

    @property
    def center(self):
        return self._x + self._w / 2, self.y + self._h / 2

    @property
    def centerx(self):
        return self._x + self._w / 2

    @property
    def centery(self):
        return self._y + self._h / 2

    @property
    def size(self):
        return self._w, self._h

    @property
    def width(self):
        return self._w

    @property
    def height(self):
        return self._h

    @property
    def w(self):
        return self._w

    @property
    def h(self):
        return self._h

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y
