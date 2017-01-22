import sys
from math import sqrt, cos, sin, pi

import pygame

__all__ = ('Task', 'Animation', 'remove_animations_of')

ANIMATION_NOT_STARTED = 0
ANIMATION_RUNNING = 1
ANIMATION_DELAYED = 2
ANIMATION_FINISHED = 3

PY2 = sys.version_info[0] == 2
string_types = None
text_type = None
if PY2:
    string_types = basestring
    text_type = unicode
else:
    string_types = text_type = str


def is_number(value):
    """Test if an object is a number.
    :param value: some object
    :returns: True
    :raises: ValueError
    """
    try:
        float(value)
    except (ValueError, TypeError):
        raise ValueError

    return True


def remove_animations_of(target, group):
    """Find animations that target objects and remove those animations

    :param target: any
    :param group: pygame.sprite.Group
    :returns: None
    """
    animations = [ani for ani in group.sprites() if isinstance(ani, Animation)]
    to_remove = [ani for ani in animations
                 if target in [i[0] for i in ani.targets]]
    group.remove(*to_remove)


class AnimBase(pygame.sprite.Sprite):
    def __init__(self):
        super(AnimBase, self).__init__()
        self._callbacks = list()

    def attach_callback(self, func):
        self._callbacks.append(func)


class Task(pygame.sprite.Sprite):
    """Execute functions at a later time and optionally loop it

    This is a silly little class meant to make it easy to create
    delayed or looping events without any complicated hooks into
    pygame's clock or event loop.

    Tasks are created and must be added to a normal pygame group
    in order to function.  This group must be updated, but not
    drawn.

        task_group = pygame.sprite.Group()

        # like a delay
        def call_later():
            pass
        task = Task(call_later, 1000)
        task_group.add(task)

        # do something 24 times at 1 second intervals
        task = Task(call_later, 1000, 24)

        # do something every 2.5 seconds forever
        task = Task(call_later, 2500, -1)

        # pass arguments
        task = Task(call_later, 1000, args=(1,2,3), kwargs={key: value})

        # chain tasks
        task = Task(call_later, 2500)
        task.chain(Task(something_else))

        When chaining tasks, do not add the chained tasks to a group.
    """

    def __init__(self, callback, interval=0, loops=1, args=None, kwargs=None):
        if not callable(callback):
            raise ValueError

        if loops < 1:
            raise ValueError

        super(Task, self).__init__()
        self.interval = interval
        self.loops = loops
        self.callback = callback
        self._duration = 0
        self._args = args if args else list()
        self._kwargs = kwargs if kwargs else dict()
        self._loops = loops
        self._chain = list()
        self._state = ANIMATION_RUNNING

    def chain(self, callback, interval=0, loops=1, args=None, kwargs=None):
        """Schedule something to be called after.  Uses same sig. as Task

        If you attempt to chain a task that will never end (loops=-1),
        then ValueError will be raised.

        :param others: Task instances
        :returns: None
        """
        return self.chain_task(Task(callback, interval=0, loops=1, args=None, kwargs=None))

    def chain_task(self, *tasks):
        """Schedule Task(s) to execute when this one is finished

        If you attempt to chain a task that will never end (loops=-1),
        then ValueError will be raised.

        :param others: Task instances
        :returns: None
        """
        if self._loops <= -1:
            raise ValueError
        for task in tasks:
            if not isinstance(task, Task):
                raise TypeError
            self._chain.append(task)
        return tasks

    def update(self, dt):
        """Update the Task

        The unit of time passed must match the one used in the
        constructor.

        Task will not 'make up for lost time'.  If an interval
        was skipped because of a lagging clock, then callbacks
        will not be made to account for the missed ones.

        :param dt: Time passed since last update.
        """
        if self._state is not ANIMATION_RUNNING:
            return
            # raise RuntimeError

        self._duration += dt
        if self._duration >= self.interval:
            self._duration -= self.interval
            if not self._loops == -1:
                self._loops -= 1
                if self._loops <= 0:
                    self.finish()
                    return

            self.callback(*self._args, **self._kwargs)

    def finish(self):
        """ Force task to finish, while executing callbacks
        """
        if self._state is ANIMATION_RUNNING:
            self._state = ANIMATION_FINISHED
            self.callback(*self._args, **self._kwargs)
            self._execute_chain()
            self._cleanup()

    def abort(self):
        """Force task to finish, without executing callbacks
        """
        self._state = ANIMATION_FINISHED
        self.kill()

    def _cleanup(self):
        self._chain = None

    def _execute_chain(self):
        groups = self.groups()
        for task in self._chain:
            task.add(*groups)


class Animation(pygame.sprite.Sprite):
    """Change numeric values over time

    To animate a target sprite/object's position, simply specify
    the target x/y values where you want the widget positioned at
    the end of the animation.  Then call start while passing the
    target as the only parameter.
        ani = Animation(x=100, y=100, duration=1000)
        ani.start(sprite)

    The shorthand method of starting animations is to pass the
    targets as positional arguments in the constructor.
        ani = Animation(sprite.rect, x=100, y=0)

    If you would rather specify relative values, then pass the
    relative keyword and the values will be adjusted for you:
        ani = Animation(x=100, y=100, duration=1000)
        ani.start(sprite, relative=True)

    You can also specify a callback that will be executed when the
    animation finishes:
        ani.callback = my_function

    Another optional callback is available that is called after
    each update:
        ani.update_callback = post_update_function

    Animations must be added to a sprite group in order for them
    to be updated.  If the sprite group that contains them is
    drawn then an exception will be raised, so you should create
    a sprite group only for containing Animations.

    You can cancel the animation by calling Animation.abort().

    When the Animation has finished, then it will remove itself
    from the sprite group that contains it.

    You can optionally delay the start of the animation using the
    delay keyword.


    Callable Attributes
    ===================

    Target values can also be callable.  In this case, there is
    no way to determine the initial value unless it is specified
    in the constructor.  If no initial value is specified, it will
    default to 0.

    Like target arguments, the initial value can also refer to a
    callable.

    NOTE: Specifying an initial value will set the initial value
          for all target names in the constructor.  This
          limitation won't be resolved for a while.


    Pygame Rects
    ============

    The 'round_values' paramenter will be set to True automatically
    if pygame rects are used as an animation target.
    """
    default_duration = 1000.
    default_transition = 'linear'

    def __init__(self, *targets, **kwargs):
        super(Animation, self).__init__()
        self.targets = list()
        self._targets = list()      #  used when there is a delay
        self.delay = kwargs.get('delay', 0)
        self._state = ANIMATION_NOT_STARTED
        self._round_values = kwargs.get('round_values', False)
        self._duration = float(kwargs.get('duration', self.default_duration))
        self._transition = kwargs.get('transition', self.default_transition)
        self._initial = kwargs.get('initial', None)
        self._relative = kwargs.get('relative', False)
        if isinstance(self._transition, string_types):
            self._transition = getattr(AnimationTransition, self._transition)
        self._elapsed = 0.
        for key in ('duration', 'transition', 'round_values', 'delay',
                    'initial', 'relative'):
            kwargs.pop(key, None)
        if not kwargs:
            raise ValueError
        self.props = kwargs

        if targets:
            self.start(*targets)

    def _get_value(self, target, name):
        """Get value of an attribute, even if it is callable

        :param target: object than contains attribute
        :param name: name of attribute to get value from
        :returns: Any
        """
        if self._initial is None:
            value = getattr(target, name)
        else:
            value = self._initial

        if callable(value):
            value = value()

        is_number(value)
        return value

    def _set_value(self, target, name, value):
        """Set a value on some other object

        If the name references a callable type, then
        the object of that name will be called with 'value'
        as the first and only argument.

        Because callables are 'write only', there is no way
        to determine the initial value.  you can supply
        an initial value in the constructor as a value or
        reference to a callable object.

        :param target: object to be modified
        :param name: name of attribute to be modified
        :param value: value
        :returns: None
        """
        if self._round_values:
            value = int(round(value, 0))

        attr = getattr(target, name)
        if callable(attr):
            attr(value)
        else:
            setattr(target, name, value)

    def update(self, dt):
        """Update the animation

        The unit of time passed must match the one used in the
        constructor.

        Make sure that you start the animation, otherwise your
        animation will not be changed during update().

        Will raise RuntimeError if animation is updated after
        it has finished.

        :param dt: Time passed since last update.
        :raises: RuntimeError
        """
        if self._state is ANIMATION_FINISHED:
            return
            # raise RuntimeError

        if self._state is not ANIMATION_RUNNING:
            return

        self._elapsed += dt
        if self.delay > 0:
            if self._elapsed > self.delay:
                self._elapsed -= self.delay
                self._gather_initial_values()
                self.delay = 0
            return

        p = min(1., self._elapsed / self._duration)
        t = self._transition(p)
        for target, props in self.targets:
            for name, values in props.items():
                a, b = values
                value = (a * (1. - t)) + (b * t)
                self._set_value(target, name, value)

        if hasattr(self, 'update_callback'):
            self.update_callback()

        if p >= 1:
            self.finish()

    def finish(self):
        """Force animation to finish, apply transforms, and execute callbacks

        Update callback will be called because the value is changed
        Final callback ('callback') will be called
        Final values will be applied
        Animation will be removed from group

        Will raise RuntimeError if animation has not been started

        :returns: None
        :raises: RuntimeError
        """
        # if self._state is not ANIMATION_RUNNING:
        #     raise RuntimeError

        if self.targets is not None:
            for target, props in self.targets:
                for name, values in props.items():
                    a, b = values
                    self._set_value(target, name, b)

        if hasattr(self, 'update_callback'):
            self.update_callback()

        self.abort()

    def abort(self):
        """Force animation to finish, without any cleanup

        Update callback will not be executed
        Final callback will be executed
        Values will not change
        Animation will be removed from group

        Will raise RuntimeError if animation has not been started

        :returns: None
        :raises: RuntimeError
        """
        # if self._state is not ANIMATION_RUNNING:
        #     raise RuntimeError

        self._state = ANIMATION_FINISHED
        self.targets = None
        self.kill()
        if hasattr(self, 'callback'):
            self.callback()

    def start(self, *targets, **kwargs):
        """Start the animation on a target sprite/object

        Targets must have the attributes that were set when
        this animation was created.

        :param targets: Any valid python object
        :raises: RuntimeError
        """
        # TODO: weakref the targets
        if self._state is not ANIMATION_NOT_STARTED:
            raise RuntimeError

        self._state = ANIMATION_RUNNING
        self._targets = targets

        if self.delay == 0:
            self._gather_initial_values()

    def _gather_initial_values(self):
        self.targets = list()
        for target in self._targets:
            props = dict()
            if isinstance(target, pygame.Rect):
                self._round_values = True
            for name, value in self.props.items():
                initial = self._get_value(target, name)
                is_number(initial)
                is_number(value)
                if self._relative:
                    value += initial
                props[name] = initial, value
            self.targets.append((target, props))

        self.update(0)


class AnimationTransition(object):
    """Collection of animation functions to be used with the Animation object.
    Easing Functions ported to Kivy from the Clutter Project
    http://www.clutter-project.org/docs/clutter/stable/ClutterAlpha.html

    The `progress` parameter in each animation function is in the range 0-1.
    """

    @staticmethod
    def linear(progress):
        return progress

    @staticmethod
    def in_quad(progress):
        return progress * progress

    @staticmethod
    def out_quad(progress):
        return -1.0 * progress * (progress - 2.0)

    @staticmethod
    def in_out_quad(progress):
        p = progress * 2
        if p < 1:
            return 0.5 * p * p
        p -= 1.0
        return -0.5 * (p * (p - 2.0) - 1.0)

    @staticmethod
    def in_cubic(progress):
        return progress * progress * progress

    @staticmethod
    def out_cubic(progress):
        p = progress - 1.0
        return p * p * p + 1.0

    @staticmethod
    def in_out_cubic(progress):
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p
        p -= 2
        return 0.5 * (p * p * p + 2.0)

    @staticmethod
    def in_quart(progress):
        return progress * progress * progress * progress

    @staticmethod
    def out_quart(progress):
        p = progress - 1.0
        return -1.0 * (p * p * p * p - 1.0)

    @staticmethod
    def in_out_quart(progress):
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p
        p -= 2
        return -0.5 * (p * p * p * p - 2.0)

    @staticmethod
    def in_quint(progress):
        return progress * progress * progress * progress * progress

    @staticmethod
    def out_quint(progress):
        p = progress - 1.0
        return p * p * p * p * p + 1.0

    @staticmethod
    def in_out_quint(progress):
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p * p
        p -= 2.0
        return 0.5 * (p * p * p * p * p + 2.0)

    @staticmethod
    def in_sine(progress):
        return -1.0 * cos(progress * (pi / 2.0)) + 1.0

    @staticmethod
    def out_sine(progress):
        return sin(progress * (pi / 2.0))

    @staticmethod
    def in_out_sine(progress):
        return -0.5 * (cos(pi * progress) - 1.0)

    @staticmethod
    def in_expo(progress):
        if progress == 0:
            return 0.0
        return pow(2, 10 * (progress - 1.0))

    @staticmethod
    def out_expo(progress):
        if progress == 1.0:
            return 1.0
        return -pow(2, -10 * progress) + 1.0

    @staticmethod
    def in_out_expo(progress):
        if progress == 0:
            return 0.0
        if progress == 1.:
            return 1.0
        p = progress * 2
        if p < 1:
            return 0.5 * pow(2, 10 * (p - 1.0))
        p -= 1.0
        return 0.5 * (-pow(2, -10 * p) + 2.0)

    @staticmethod
    def in_circ(progress):
        return -1.0 * (sqrt(1.0 - progress * progress) - 1.0)

    @staticmethod
    def out_circ(progress):
        p = progress - 1.0
        return sqrt(1.0 - p * p)

    @staticmethod
    def in_out_circ(progress):
        p = progress * 2
        if p < 1:
            return -0.5 * (sqrt(1.0 - p * p) - 1.0)
        p -= 2.0
        return 0.5 * (sqrt(1.0 - p * p) + 1.0)

    @staticmethod
    def in_elastic(progress):
        p = .3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        q -= 1.0
        return -(pow(2, 10 * q) * sin((q - s) * (2 * pi) / p))

    @staticmethod
    def out_elastic(progress):
        p = .3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        return pow(2, -10 * q) * sin((q - s) * (2 * pi) / p) + 1.0

    @staticmethod
    def in_out_elastic(progress):
        p = .3 * 1.5
        s = p / 4.0
        q = progress * 2
        if q == 2:
            return 1.0
        if q < 1:
            q -= 1.0
            return -.5 * (pow(2, 10 * q) * sin((q - s) * (2.0 * pi) / p))
        else:
            q -= 1.0
            return pow(2, -10 * q) * sin((q - s) * (2.0 * pi) / p) * .5 + 1.0

    @staticmethod
    def in_back(progress):
        return progress * progress * ((1.70158 + 1.0) * progress - 1.70158)

    @staticmethod
    def out_back(progress):
        p = progress - 1.0
        return p * p * ((1.70158 + 1) * p + 1.70158) + 1.0

    @staticmethod
    def in_out_back(progress):
        p = progress * 2.
        s = 1.70158 * 1.525
        if p < 1:
            return 0.5 * (p * p * ((s + 1.0) * p - s))
        p -= 2.0
        return 0.5 * (p * p * ((s + 1.0) * p + s) + 2.0)

    @staticmethod
    def _out_bounce_internal(t, d):
        p = t / d
        if p < (1.0 / 2.75):
            return 7.5625 * p * p
        elif p < (2.0 / 2.75):
            p -= (1.5 / 2.75)
            return 7.5625 * p * p + .75
        elif p < (2.5 / 2.75):
            p -= (2.25 / 2.75)
            return 7.5625 * p * p + .9375
        else:
            p -= (2.625 / 2.75)
            return 7.5625 * p * p + .984375

    @staticmethod
    def _in_bounce_internal(t, d):
        return 1.0 - AnimationTransition._out_bounce_internal(d - t, d)

    @staticmethod
    def in_bounce(progress):
        return AnimationTransition._in_bounce_internal(progress, 1.)

    @staticmethod
    def out_bounce(progress):
        return AnimationTransition._out_bounce_internal(progress, 1.)

    @staticmethod
    def in_out_bounce(progress):
        p = progress * 2.
        if p < 1.:
            return AnimationTransition._in_bounce_internal(p, 1.) * .5
        return AnimationTransition._out_bounce_internal(p - 1., 1.) * .5 + .5
