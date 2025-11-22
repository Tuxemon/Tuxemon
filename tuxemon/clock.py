# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable
from heapq import heapify, heappop, heappush
from typing import Callable, Optional


class AsyncScheduledItem:
    def __init__(
        self,
        func: Callable[[float], Awaitable[Optional[bool]]],
        delay: float,
        repeat: bool = False,
        soft: bool = False,
    ) -> None:
        self.func = func
        self.delay = delay
        self.repeat = repeat
        self.soft = soft
        self.last_ts: float = time.perf_counter()
        self.next_ts: float = self.last_ts + delay

    def __lt__(self, other: AsyncScheduledItem) -> bool:
        return self.next_ts < other.next_ts


class AsyncScheduler:
    def __init__(self) -> None:
        self._items: list[AsyncScheduledItem] = []
        self._scale: float = 1.0
        self._last_ts: float = time.perf_counter()
        self._intervals: list[float] = []
        self.cumulative_time: float = 0.0

    def set_time_scale(self, scale: float) -> None:
        self._scale = max(0.0, scale)

    def get_time_scale(self) -> float:
        return self._scale

    def _get_soft_next_ts(self, last_ts: float, interval: float) -> float:
        """Find a non-colliding next_ts by nudging forward."""
        next_ts = last_ts + interval
        epsilon = interval / 4.0
        taken = any(
            abs(item.next_ts - next_ts) <= epsilon for item in self._items
        )
        if not taken:
            return next_ts

        # Try subdividing interval to find a free slot
        dt = interval
        divs = 1
        while divs <= 16:
            candidate = last_ts
            for _ in range(divs - 1):
                candidate += dt
                if not any(
                    abs(item.next_ts - candidate) <= dt / 4.0
                    for item in self._items
                ):
                    return candidate
            dt /= 2
            divs *= 2
        return next_ts

    def schedule(
        self,
        func: Callable[[float], Awaitable[Optional[bool]]],
        delay: float,
        repeat: bool = False,
        soft: bool = False,
    ) -> AsyncScheduledItem:
        last_ts = self._last_ts
        next_ts = last_ts + delay
        if soft and delay > 0.0:
            next_ts = self._get_soft_next_ts(last_ts, delay)

        item = AsyncScheduledItem(func, delay, repeat, soft)
        item.next_ts = next_ts
        heappush(self._items, item)
        return item

    def unschedule(self, item: AsyncScheduledItem) -> None:
        """Remove a scheduled task."""
        try:
            self._items.remove(item)
            heapify(self._items)
        except ValueError:
            pass

    async def run(self) -> None:
        """Central dispatcher: runs tasks in order of next_ts."""
        while self._items:
            item = self._items[0]  # peek at soonest
            sleep_time = (
                max(item.next_ts - time.perf_counter(), 0.0) / self._scale
            )
            await asyncio.sleep(sleep_time)

            heappop(self._items)
            dt = time.perf_counter() - item.last_ts
            item.last_ts = time.perf_counter()

            try:
                retval = await item.func(dt)
            except Exception as e:
                print(f"Task error: {e}")
                retval = False

            if item.repeat and retval is not False:
                if item.soft and item.delay > 0.0:
                    item.next_ts = self._get_soft_next_ts(
                        item.last_ts, item.delay
                    )
                else:
                    item.next_ts = item.last_ts + item.delay
                heappush(self._items, item)

    async def tick_rate(self, rate: float) -> float:
        """Maintain a target tick rate (like Clock.tick_rate)."""
        current_ts = time.perf_counter()
        target_ts = self._last_ts + (1.0 / rate)
        sleep_time = max(target_ts - current_ts, 0.0)
        await asyncio.sleep(sleep_time)

        now = time.perf_counter()
        delta_t = now - self._last_ts
        self._last_ts = now
        self._intervals.append(delta_t)
        if len(self._intervals) > 10:
            self._intervals.pop(0)
        return delta_t

    def get_fps(self) -> float:
        """Frames per second based on tick intervals."""
        if not self._intervals:
            return 0.0
        avg_interval = sum(self._intervals) / len(self._intervals)
        return 1.0 / avg_interval if avg_interval > 0 else 0.0


class MobileAsyncScheduler(AsyncScheduler):
    def __init__(self) -> None:
        super().__init__()
        self._is_active = True
        self._max_background_fps = 5.0

    def set_active_state(self, active: bool) -> None:
        self._is_active = active

    async def run(self) -> None:
        """Central dispatcher with background/foreground logic."""
        while self._items:
            item = self._items[0]
            now = time.perf_counter()

            # Catch-up if returning from background
            if self._is_active and (now - self._last_ts) > 5.0:
                await self._catch_up_tick()
                continue

            # Background FPS limiting
            if not self._is_active and self._max_background_fps > 0:
                sleep_duration = max(
                    0.0,
                    (1.0 / self._max_background_fps) - (now - self._last_ts),
                )
                await asyncio.sleep(sleep_duration)

            # Normal dispatch
            sleep_time = max(item.next_ts - now, 0.0) / self._scale
            await asyncio.sleep(sleep_time)

            heappop(self._items)
            dt = time.perf_counter() - item.last_ts
            item.last_ts = time.perf_counter()
            try:
                retval = await item.func(dt)
            except Exception as e:
                print(f"Task error: {e}")
                retval = False

            if item.repeat and retval is not False:
                if item.soft and item.delay > 0.0:
                    item.next_ts = self._get_soft_next_ts(
                        item.last_ts, item.delay
                    )
                else:
                    item.next_ts = item.last_ts + item.delay
                heappush(self._items, item)

    async def _catch_up_tick(self) -> None:
        """Process missed events after inactivity with normalized dt."""
        now = time.perf_counter()
        long_delta_t = now - self._last_ts
        self.cumulative_time += long_delta_t
        self._last_ts = now

        for item in list(self._items):
            if item.next_ts <= now:
                await item.func(item.delay if item.repeat else 0.0)
                if item.repeat:
                    item.last_ts = now
                    item.next_ts = now + item.delay
        heapify(self._items)


class HistoricalAsyncScheduler(AsyncScheduler):
    def __init__(self, initial_time: float = 0.0):
        super().__init__()
        self._virtual_time = initial_time
        self._is_paused = False

    def get_virtual_time(self) -> float:
        return self._virtual_time

    async def step_forward(self, dt: float) -> None:
        """Advance virtual time deterministically and update FPS stats."""
        self._virtual_time += dt
        self._last_ts = self._virtual_time
        self.cumulative_time += dt
        self._intervals.append(dt)
        if len(self._intervals) > 10:
            self._intervals.pop(0)

        # Run scheduled tasks that are due
        for item in list(self._items):
            if item.next_ts <= self._virtual_time:
                await item.func(dt)
                if item.repeat:
                    item.next_ts = self._virtual_time + item.delay
