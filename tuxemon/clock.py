# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import collections
import time
from collections.abc import Callable
from heapq import heapify, heappop, heappush, heappushpop
from typing import Any, Deque, Optional, Union

__all__ = ("ScheduledItem", "Scheduler", "Clock")


class ScheduledItem:
    """A class that describes a scheduled callback.

    This class is never created by the user; instead, pygame creates and
    returns an instance of this class when scheduling a callback.

    If you hold on to instance of this class, do not modify any values of it.
    """

    __slots__ = ["func", "interval", "last_ts", "next_ts"]

    def __init__(
        self, func: Any, last_ts: float, next_ts: float, interval: float
    ) -> None:
        self.func = func
        self.interval = interval
        self.last_ts = last_ts
        self.next_ts = next_ts

    def __lt__(self, other: Any) -> Any:
        try:
            return self.next_ts < other.next_ts
        except AttributeError:
            return self.next_ts < other


class Scheduler:
    """Class for scheduling functions."""

    def __init__(self, time_function: Callable[[], float] = time.perf_counter):
        """Initialise a Clock, with optional custom time function.
        :Parameters:
            `time_function` : function
                Function to return the elapsed time of the application,
                in time units.
        """
        super().__init__()
        self._time = time_function
        self._last_ts: float = -1
        self._times: Deque[int] = collections.deque(maxlen=10)
        self._scheduled_items: list[ScheduledItem] = []
        self._next_tick_items: list[ScheduledItem] = []
        self.cumulative_time = 0.0

    def _get_nearest_ts(self) -> Union[float, int]:
        """Schedule from now, unless now is sufficiently close to last_ts, in
        which case use last_ts.  This clusters together scheduled items that
        probably want to be scheduled together.
        """
        last_ts = self._last_ts
        ts = self._time()
        if ts - last_ts > 0.2:
            last_ts = ts
        return last_ts

    def _get_soft_next_ts(self, last_ts: float, interval: float) -> float:
        def taken(ts: float, e: float) -> bool:
            """Return True if the given time has already got an item
            scheduled nearby.
            """
            for item in self._scheduled_items:
                if item.next_ts is None:
                    continue
                elif abs(item.next_ts - ts) <= e:
                    return True
                elif item.next_ts > ts + e:
                    return False
            return False

        next_ts = last_ts + interval
        if not taken(next_ts, interval / 4):
            return next_ts

        dt = interval
        divs = 1
        while True:
            next_ts = last_ts
            for i in range(divs - 1):
                next_ts += dt
                if not taken(next_ts, dt / 4.0):
                    return next_ts
            dt /= 2
            divs *= 2

            # Avoid infinite loop in pathological case
            if divs > 16:
                return next_ts

    def schedule(
        self,
        func: Any,
        delay: float = 0.0,
        repeat: bool = False,
        soft: bool = False,
    ) -> ScheduledItem:
        """
        Schedule a function to be run sometime in the future.

        The function should have a prototype that includes ``dt`` as the
        first argument, which gives the elapsed time, in time units, since the
        last clock tick.

            def callback(dt):
                pass


        Limitations
        ===========

        There is a hard limit of 10 items that can be scheduled on
        next tick.  This limit reduces the power and performance
        impact of the clock on mobile and battery operated computers.

        A runtime error will be raised if the maximum is reached.


        Unscheduling
        ============

        If callback returns False (not None), then it will not be
        scheduled again.


        Soft Scheduling
        ===============

        This is useful for functions that need to be called regularly,
        but not relative to the initial start time.
        for example: events which need to occur regularly -- if all audio
        updates are scheduled at the same time
        (for example, mixing several tracks of a music score, or playing
        multiple videos back simultaneously), the resulting load on the
        CPU is excessive for those intervals but idle outside.  Using
        the soft interval scheduling, the load is more evenly distributed.

        Parameters:
            func: Function to be called
            delay: Delay in time unit until it is called
            repeat: Function will be repeated every 'delay' units
            soft: See notes about Soft Scheduling

        Returns:
            Reference to scheduled item

        """
        last_ts = self._get_nearest_ts()
        if soft:
            assert delay > 0.0
            next_ts = self._get_soft_next_ts(last_ts, delay)
            last_ts = next_ts - delay
        next_ts = last_ts + delay

        interval = delay if repeat else 0.0

        item = ScheduledItem(func, last_ts, next_ts, interval)
        if next_ts == 0.0:
            self._next_tick_items.append(item)
            if len(self._next_tick_items) > 10:
                raise RuntimeError
        else:
            heappush(self._scheduled_items, item)
        return item

    def tick(self) -> float:
        """
        Cause clock to update and call scheduled functions.

        This updates the clock's internal measure of time and returns
        the difference since the last update (or since the clock was created).

        Will call any scheduled functions that have elapsed.

        Returns:
            The number of time units since the last "tick", or 0 if this
            was the first tick.

        """
        delta_t = self.set_time(self._time())
        self._times.append(int(delta_t))
        self.call_scheduled_functions(delta_t)
        return delta_t

    def get_interval(self) -> float:
        """Get the average amount of time passed between each tick.

        Useful for calculating FPS if this clock is used with the display.
        Returned value is averaged from last 10 ticks.

        Value will be 0.0 if before 1st tick.

        :rtype: float
        :return: Average amount of time passed between each tick
        """
        try:
            return sum(self._times) / len(self._times)
        except ZeroDivisionError:
            return 0.0

    def set_time(self, time_stamp: float) -> float:
        """
        Set the clock manually and do not call scheduled functions.  Return
        the difference in time from the last time clock was updated.

        Parameters:
            time_stamp: This will become the new value of the clock.  Setting the clock
            to negative values will have undefined results.

        Returns:
            The number of time units since the last update, or 0.0 if this
            was the first update.

        """
        # self._last_ts will be -1 before first time set
        if self._last_ts < 0:
            delta_t = 0.0
            self._last_ts = time_stamp
        else:
            delta_t = time_stamp - self._last_ts
        self.cumulative_time += delta_t
        self._last_ts = time_stamp
        return delta_t

    def call_scheduled_functions(self, dt: float) -> bool:
        """
        Call scheduled functions that elapsed on the last `update_time`.

        Parameters:
            dt: The elapsed time since the last update to pass to each
            scheduled function.

        Returns:
            Returns True if any functions were called, otherwise False.
        """
        scheduled_items = self._scheduled_items
        now = self._last_ts
        result = False

        # handle items scheduled for next tick
        if self._next_tick_items:
            result = True
            for item in list(self._next_tick_items):
                retval = item.func(dt)
                # do not change the following line to "if not retval"!
                # some items will return None, but False is a special value
                if retval == False:
                    self._next_tick_items.remove(item)

        # check the next scheduled item that is not called each tick
        # if it is scheduled in the future, then exit
        try:
            item = scheduled_items[0]
            if item.next_ts > now:
                return result
        except IndexError:
            return result

        # we have at least one item that is due to be called
        result = True
        get_soft_next_ts = self._get_soft_next_ts

        # wherever this value is true the current item will be pushed
        # into the heap.  it essentially means that the current
        # scheduled item is important and needs stay scheduled.
        replace = False

        while scheduled_items:
            # get the next item to be called
            head = scheduled_items[0]

            # if next item is scheduled in the future then exit while
            # taking care of the heap
            if head.next_ts > now:
                if replace:
                    heappush(scheduled_items, item)
                replace = False
                break

            # the scheduler will hold onto a reference to an item in
            # case it needs to be rescheduled.  it is more efficient
            # to push and pop the heap in one call than to make two
            # calls.
            if replace:
                item = heappushpop(scheduled_items, item)
            else:
                item = heappop(scheduled_items)

            # call the function associated with the scheduled item
            retval = item.func(now - item.last_ts)

            if item.interval:
                # callbacks can unschedule themselves by returning false
                replace = not retval == False
                item.next_ts = item.last_ts + item.interval
                item.last_ts = now

                # the execution time of this item has already passed
                # so it must be rescheduled
                if item.next_ts <= now:
                    if now - item.next_ts < 0.05:
                        item.next_ts = now + item.interval
                    else:
                        # missed by significant amount, do a soft reschedule
                        # to avoid lumping everything together
                        # in this case, the next dt will not be accurate
                        item.next_ts = get_soft_next_ts(now, item.interval)
                        item.last_ts = item.next_ts - item.interval
            else:
                # replace is False, so this item will not be rescheduled
                replace = False

        # it is possible that the loop exited while an important item
        # was waiting to be pushed into the heap.
        if replace:
            heappush(scheduled_items, item)

        return result

    def get_idle_time(self) -> Optional[float]:
        """
        Get the time until the next item is scheduled.

        Returns:
            Time until the next scheduled event in time units, or ``None``
            if there is no event scheduled.
        """
        if self._next_tick_items:
            return 0.0

        try:
            next_ts = self._scheduled_items[0].next_ts
            return max(next_ts - self._time(), 0.0)
        except IndexError:
            return None

    def unschedule(self, func: Any) -> None:
        """
        Remove a function from the schedule.

        If the function appears in the schedule more than once, all occurrences
        are removed.  If the function was not scheduled, no error is raised.

        Parameters:
            func: The function to remove from the schedule.

        """

        def remove(list_: list[ScheduledItem]) -> bool:
            resort = False
            remove_ = list_.remove
            for i in list(i for i in list_ if i.func is func):
                remove_(i)
                resort = True
            return resort

        remove(self._next_tick_items)
        if remove(self._scheduled_items):
            # this will restructure the heap
            heapify(self._scheduled_items)


class Clock(Scheduler):
    """Schedules stuff like a Scheduler, and includes time limiting functions

    WIP
    """

    @staticmethod
    def _least_squares(
        gradient: int = 1,
        offset: int = 0,
    ) -> Any:
        """
        source: pyglet.app.App

        Parameters:
            gradient:
            offset:

        """
        X = 0
        Y = 0
        XX = 0
        XY = 0
        n = 0

        x, y = yield gradient, offset
        X += x
        Y += y
        XX += x * x
        XY += x * y
        n += 1

        while True:
            x, y = yield gradient, offset
            X += x
            Y += y
            XX += x * x
            XY += x * y
            n += 1

            try:
                gradient = int((n * XY - X * Y) / (n * XX - X * X))
                offset = int((Y - gradient * X) / n)
            except ZeroDivisionError:
                # Can happen in pathological case; keep current
                # gradient/offset for now.
                pass
