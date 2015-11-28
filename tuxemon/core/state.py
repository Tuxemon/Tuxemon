import os
import sys
import inspect
from collections import OrderedDict
from importlib import import_module


class StateManager(object):
    def __init__(self, package):
        self.package = package
        self.state_dict = dict()

    def auto_discovery(self):
        """ Scan a folder, load states found in it, and register them
        """
        state_folder = os.path.join(*self.package.split('.'))
        exclude_endings = (".py", ".pyc", "__pycache__")
        for folder in os.listdir(state_folder):
            if any(folder.endswith(end) for end in exclude_endings):
                continue
            for state in self.collect_states_from_path(folder):
                self.register_state(state)

    def register_state(self, state):
        """ Add a state class

        :param state: any subclass of core.state.State
        """
        name = state.__name__
        if name in self.state_dict:
            print('Duplicate state detected: {}'.format(name))
            raise RuntimeError
        self.state_dict[name] = state

    @staticmethod
    def collect_states_from_module(import_name):
        """ Given a module, return all classes in it that are a game state
        """
        classes = inspect.getmembers(sys.modules[import_name], inspect.isclass)
        state_classes = [i[1] for i in classes if issubclass(i[1], State)]
        for state in state_classes:
            yield state

    def collect_states_from_path(self, folder):
        """ Load a state from disk, but do not register it

        :param folder: folder to load from
        :return: Instanced state
        """
        # TODO: not hardcode package name
        try:
            import_name = self.package + '.' + folder
            import_module(import_name)
            for state in self.collect_states_from_module(import_name):
                yield state
        except Exception as e:
            template = "{} failed to load or is not a valid game package"
            print(e)
            print(template.format(folder))
            raise

    def query_all_states(self):
        """ Return a dictionary of all loaded states

        Keys are state names, values are State classes

        :return: dictionary of all loaded states
        """
        return self.state_dict.copy()

    def start_state(self, state_name, persist=None):
        """ Start a state

        New stats will be created if there are none.

        :param state_name: name of state to start
        :param persist: dictionary of data for state
        :return: None
        """
        if persist is None:
            persist = self.create_new_persist()

        try:
            state = self.state_dict[state_name]
        except KeyError:
            print('Cannot find state: {}'.format(state_name))
            raise RuntimeError

        instance = state(self)
        # instance.controller = self
        instance.startup(self.current_time, persist)

        self.state = instance
        self.state_name = state_name

    def create_new_games_stats(self):
        """ Create new dict suitable for use when creating CasinoPlayer

        Dict will contain all stats from any game that logs stats

        :return: dict
        """
        stats = dict()

        # if the stats system is desired, use the following code:
        # for name, state in self.state_dict.items():
        #     func = getattr(state, 'initialize_stats', None)
        #     if func:
        #         game_stats = func()
        #         stats[name] = game_stats

        return stats

    @staticmethod
    def create_persist_from_stats(stats):
        persist = OrderedDict()
        return persist

    def create_new_persist(self):
        """ Create new stats dictionary suitable for use as state persist

        Default persist for all states will be new
        Stats will be default from the states

        :return: None
        """
        stats = self.create_new_games_stats()
        return self.create_persist_from_stats(stats)

    def flip_state(self):
        """
        When a State changes to done necessary startup and cleanup functions
        are called and the current State is changed.
        """
        previous, self.state_name = self.state_name, self.state.next
        persist = self.state.cleanup()
        self.start_state(self.state_name, persist)
        self.state.previous = previous


class State(object):
    """This is a prototype class for States.  All states should inherit from it.
    No direct instances of this class should be created. get_event and update
    must be overloaded in the child class.  startup and cleanup need to be
    overloaded when there is data that must persist between States.

    """
    def __init__(self):
        self.start_time = 0.0
        self.current_time = 0.0
        self.done = False
        self.quit = False
        self.next = None
        self.previous = None
        self.persist = {}
        self.menu_blocking = False

    def get_event(self, event):
        """Processes events that were passed from the main event loop.
        Must be overridden in children.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """
        pass

    def startup(self, current_time, persistant):
        """Add variables passed in persistant to the proper attributes and
        set the start time of the State to the current time.

        :param current_time: Current time passed.
        :param persistant: Keep a dictionary of optional persistant variables.

        :type current_time: Integer
        :type persistant: Dictionary

        :rtype: None
        :returns: None


        **Examples:**

        >>> current_time
        2895
        >>> persistant
        {}
        """

        self.persist = persistant
        self.start_time = current_time

    def shutdown(self):
        """Called when State.done is set to True.

        :param current_time: Current time passed.
        :param persistant: Keep a dictionary of optional persistant variables.

        :type current_time: Integer
        :type persistant: Dictionary

        :rtype: None
        :returns: None


        **Examples:**

        >>> current_time
        2895
        >>> persistant
        {}

        """
        pass

    def cleanup(self):
        """Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.

        :param None:

        :rtype: Dictionary
        :returns: Persist dictionary of variables.

        """
        self.done = False
        self.shutdown()
        return self.persist

    def update(self, surface, keys, current_time):
        """Update function for state.  Must be overloaded in children.

        :param surface: The pygame.Surface of the screen to draw to.
        :param keys: List of keys from pygame.event.get().
        :param current_time: The amount of time that has passed.

        :type surface: pygame.Surface
        :type keys: Tuple
        :type current_time: Integer

        :rtype: None
        :returns: None

        **Examples:**

        >>> surface
        <Surface(1280x720x32 SW)>
        >>> keys
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ...
        >>> current_time
        435

        """
        pass

    def render_font(self, font, msg, color, center):
        """Returns the rendered font surface and its rect centered on center."""
        msg = font.render(msg, 1, color)
        rect = msg.get_rect(center=center)
        return msg, rect
