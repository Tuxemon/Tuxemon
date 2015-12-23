import inspect
import os
import sys
from abc import ABCMeta, abstractmethod
from importlib import import_module
from core import prepare


class State(object):
    """ This is a prototype class for States.

    All states should inherit from it. No direct instances of this
    class should be created. get_event and update must be overloaded
    in the child class.

    Overview of Methods:
       startup - Called when added to the state stack
       resume - Called each time state is updated for first time
       update - Called each frame while state is active
       get_event
       pause - Called when state is not destroyed, but also not active
       shutdown - Called before state is destroyed

    """
    __metaclass__ = ABCMeta

    def __init__(self, control):
        """ Do no override this unless there is a special need.

        All init for the State, loading of config, images, etc should
        be done in State.startup or State.resume, not here.

        :param control: State Manager / Control / Game... all the same
        :return: None
        """
        self.game = control   # TODO: rename 'game' to 'control'
        self.start_time = 0.0
        self.current_time = 0.0
        self.menu_blocking = False

    @abstractmethod
    def get_event(self, event):
        """ Processes events that were passed from the main event loop.
        Must be overridden in children.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """
        pass

    @abstractmethod
    def update(self, screen, keys, current_time, time_delta):
        """ Update function for state.  Must be overloaded in children.

        :param screen: The pygame.Surface of the screen to draw to.
        :param keys: List of keys from pygame.event.get().
        :param current_time: The amount of time that has passed.

        :type screen: pygame.Surface
        :type keys: Tuple
        :type current_time: Integer

        :rtype: None
        :returns: None

        **Examples:**

        >>> screen
        <Surface(1280x720x32 SW)>
        >>> keys
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ...
        >>> current_time
        435

        """
        pass

    def startup(self, params=None):
        """ Called when scene is added to State Stack

        This will be called:
        * after state is pushed and before next update
        * just once during the life of a state

        Example uses: loading images, configuration, sounds.

        :param params: Configuration options

        """
        pass

    def resume(self):
        """ Called before update when state is newly in focus

        This will be called:
        * before update after being pushed to the stack
        * before update after state has been paused
        * state will begin to accept player input
        * could be called several times over lifetime of state

        Example uses: starting music, playing state transition, open menu
        """
        pass

    def pause(self):
        """ Called when state is pushed back in the stack, allowed to pause

        This will be called:
        * after update when state is pushed back
        * when state is no longer accepting player input
        * could be called several times over lifetime of state

        Example uses: stopping music, sounds, fading out, making state graphics dim
        """
        pass

    def shutdown(self):
        """ Called when state is removed from stack and will be destroyed

        This will be called:
        * after update when state is popped

        Make sure to release any references to objects that may cause
        cyclical dependencies.
        """
        pass


class StateManager(object):
    """ Mix-in style class for use with Control class.

    This is currently undergoing a refactor of sorts, API may not be stable
    """

    def __init__(self):
        """ Currently no need to call __init__
            function is declared to provide IDE with some info on the class only
            this may change in the future, do not rely on this behaviour
        """
        self.state_stack = list()
        self.state_dict = dict()
        self.done = False
        self.current_time = 0.0
        self.package = ""

    def auto_state_discovery(self):
        """ Scan a folder, load states found in it, and register them
        """
        state_folder = prepare.BASEDIR + os.path.join(*self.package.split('.'))
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

    def pop_state(self):
        """ Pop the currently running state.  The previously running state will resume.

        :return:
        """
        try:
            previous = self.state_stack.pop(0)
            previous.shutdown()

            if self.state_stack:
                self.current_state.resume()
            else:
                # TODO: make API for quiting the app main loop
                self.done = True
                self.exit = True

        except IndexError:
            print("Attempted to pop state when no state was active.")
            raise RuntimeError

    def push_state(self, state_name, params=None):
        """ Start a state

        New stats will be created if there are none.

        :param state_name: name of state to start
        :param params: dictionary of data used to init the state
        :param persist: dictionary of data for shared state
        :return: instanced State
        """
        try:
            state = self.state_dict[state_name]
        except KeyError:
            print('Cannot find state: {}'.format(state_name))
            raise RuntimeError

        previous = self.current_state
        if previous is not None:
            previous.pause()

        instance = state(self)
        instance.controller = self
        instance.startup(params)

        self.state_stack.insert(0, instance)

        return instance

    @property
    def state_name(self):
        """ Name of state currently running

        TODO: phase this out?

        :return: string
        """
        return self.state_stack[0].__class__.__name__

    @property
    def current_state(self):
        """ The currently running state

        :return: State
        """
        try:
            return self.state_stack[0]
        except IndexError:
            return None
