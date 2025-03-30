# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
# Based on pyganim: A sprite animation module for Pygame.
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pyganim
# Released under a "Simplified BSD" license
from __future__ import annotations

import bisect
import itertools
from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal, Optional, TypeVar, Union

# TODO: Feature idea: if the same image file is specified, re-use the Surface
import pygame

# setting up constants
from pygame.rect import Rect

PLAYING: Final = "playing"
PAUSED: Final = "paused"
STOPPED: Final = "stopped"

State = Literal["playing", "paused", "stopped"]


class SurfaceAnimation:
    """
    Animation of Pygame surfaces. Starts off in the STOPPED state.

    Parameters:
        frames: A list of tuples (image, duration) for each frame of
            animation, where image can be either a Pygame surface or a
            path to an image, and duration is the duration in seconds.
            Note that the images and duration cannot be changed. A new
            SurfaceAnimation object will have to be created.
        loop: Tells the animation object to keep playing in a loop.

    """

    def __init__(
        self,
        frames: Sequence[tuple[Union[str, pygame.surface.Surface], float]],
        loop: bool = True,
    ) -> None:
        # Obtain constant precision setting the initial value to 2^32:
        # https://randomascii.wordpress.com/2012/02/13/dont-store-that-in-a-float/
        self._internal_clock = float(2**32)

        # _images stores the pygame.Surface objects of each frame
        self._images = []

        # _durations stores the durations (in seconds) of each frame.
        # e.g. [1, 1, 2.5] means the first and second frames last one second,
        # and the third frame lasts for two and half seconds.
        self._durations = []

        self._state: State = STOPPED
        self._loop = loop
        self._rate = 1.0
        self._visibility = True

        # The time that the play() function was last called.
        self._playing_start_time = 0.0

        # The time that the pause() function was last called.
        self._paused_start_time = 0.0

        if not frames:
            raise ValueError("Must contain at least one frame.")

        # Load each frame of animation into _images
        for i, frame in enumerate(frames):
            if not isinstance(frame, tuple) or len(frame) != 2:
                raise ValueError(f"Frame {i} has incorrect format.")
            if not isinstance(frame[0], (str, pygame.Surface)):
                raise ValueError(
                    f"Frame {i} image must be a string filename or a pygame.Surface"
                )
            if frame[1] <= 0:
                raise ValueError(
                    f"Frame {i} duration must be greater than zero."
                )

            frame_img = (
                pygame.image.load(frame[0])
                if isinstance(frame[0], str)
                else frame[0]
            )
            self._images.append(frame_img)
            self._durations.append(frame[1])

        # _start_times shows when each frame begins. len(self._start_times)
        # will always be one more than len(self._images), because the last
        # number will be when the last frame ends, rather than when it starts.
        # The values are in seconds.
        # So self.duration tells you the length of the entire
        # animation. e.g. if _durations is [1, 1, 2.5], then _start_times will
        # be [0, 1, 2, 4.5]
        self._start_times = (0.0,) + tuple(
            itertools.accumulate(self._durations),
        )

    def get_frame(self, frame_num: int) -> pygame.surface.Surface:
        """Return the pygame.Surface object of the frame_num-th frame."""
        from tuxemon.sprite import dummy_image

        if frame_num >= len(self._images):
            return dummy_image

        return self._images[frame_num]

    def get_current_frame(self) -> pygame.surface.Surface:
        """Return the current frame."""
        return self.get_frame(self.frames_played)

    def is_finished(self) -> bool:
        """Return ``True`` if this animation has finished playing."""
        return not self.loop and self.elapsed >= self.duration

    def play(self, start_time: Optional[float] = None) -> None:
        """Start playing the animation."""
        if start_time is None:
            start_time = self._internal_clock

        if self._state == PLAYING:
            if self.is_finished():
                # if the animation doesn't loop and has already finished, then
                # calling play() causes it to replay from the beginning.
                self._playing_start_time = start_time
        elif self._state == STOPPED:
            # if animation was stopped, start playing from the beginning
            self._playing_start_time = start_time
        elif self._state == PAUSED:
            # if animation was paused, start playing from where it was paused
            self._playing_start_time = start_time - (
                self._paused_start_time - self._playing_start_time
            )
        self._state = PLAYING

    def pause(self, start_time: Optional[float] = None) -> None:
        """Stop having the animation progress."""
        if start_time is None:
            start_time = self._internal_clock

        if self._state == PAUSED:
            return  # do nothing
        elif self._state == PLAYING:
            self._paused_start_time = start_time
        elif self._state == STOPPED:
            rightNow = self._internal_clock
            self._playing_start_time = rightNow
            self._paused_start_time = rightNow
        self._state = PAUSED

    def stop(self) -> None:
        """Reset the animation to the beginning frame, and stop."""
        if self._state == STOPPED:
            return  # do nothing
        self._state = STOPPED

    def update(self, time_delta: float) -> None:
        """
        Update the internal clock with the elapsed time.

        Parameters:
            time_delta: Time elapsed since last call to update.

        """
        self._internal_clock += time_delta

    def flip(self, flip_axes: str) -> None:
        """Flip all frames of an animation along the X-axis and/or Y-axis."""
        # Empty string - animation won't be flipped
        flip_x = "x" in flip_axes
        flip_y = "y" in flip_axes

        self._images = [
            pygame.transform.flip(image, flip_x, flip_y)
            for image in self._images
        ]

    def _get_max_size(self) -> tuple[int, int]:
        """
        Get the maximum size of the animation.

        Goes through all the Surface objects in this animation object
        and returns the max width and max height that it finds, as these
        widths and heights may be on different Surface objects.

        Returns:
            Max size in the form (width, height).

        """
        frame_widths = []
        frame_heights = []
        for i in range(len(self._images)):
            frameWidth, frameHeight = self._images[i].get_size()
            frame_widths.append(frameWidth)
            frame_heights.append(frameHeight)
        maxWidth = max(frame_widths)
        maxHeight = max(frame_heights)

        return (maxWidth, maxHeight)

    def get_rect(self) -> pygame.rect.Rect:
        """
        Returns a Rect object for this animation object.

        The top and left will be set to 0, 0, and the width and height
        will be set to the maximum size of the animation.

        Returns:
            Rect object of maximum size.

        """
        maxWidth, maxHeight = self._get_max_size()
        return Rect(0, 0, maxWidth, maxHeight)

    @property
    def rate(self) -> float:
        return self._rate

    @rate.setter
    def rate(self, rate: float) -> None:
        rate = float(rate)
        if rate < 0:
            raise ValueError("rate must be greater than 0.")
        self._rate = rate

    @property
    def loop(self) -> bool:
        return self._loop

    @loop.setter
    def loop(self, loop: bool) -> None:
        if self.state == PLAYING and self._loop and not loop:
            # If we are turning off looping while the animation is playing,
            # we need to modify the _playing_start_time so that the rest of
            # the animation will play, and then stop. Otherwise, the
            # animation will immediately stop playing if it has already looped.
            self._playing_start_time = self._internal_clock - self.elapsed
        self._loop = bool(loop)

    @property
    def state(self) -> State:
        if self.is_finished():
            # If finished playing, then set state to STOPPED.
            self._state = STOPPED

        return self._state

    @state.setter
    def state(self, state: State) -> None:
        if state not in (PLAYING, PAUSED, STOPPED):
            raise ValueError(
                "state must be one of surfanim.PLAYING, surfanim.PAUSED, or "
                "surfanim.STOPPED",
            )
        if state == PLAYING:
            self.play()
        elif state == PAUSED:
            self.pause()
        elif state == STOPPED:
            self.stop()

    @property
    def visibility(self) -> bool:
        return self._visibility

    @visibility.setter
    def visibility(self, visibility: bool) -> None:
        self._visibility = bool(visibility)

    @property
    def elapsed(self) -> float:
        # NOTE: Do to floating point rounding errors, this doesn't work
        # precisely.

        # To prevent infinite recursion, don't use the self.state property,
        # just read/set self._state directly because the state getter calls
        # this method.

        # Find out how long ago the play()/pause() functions were called.
        if self._state == STOPPED:
            # if stopped, then just return 0
            return 0

        if self._state == PLAYING:
            # If playing, then draw the current frame (based on when the
            # animation started playing). If not looping and the animation
            # has gone through all the frames already, then draw the last
            # frame.
            elapsed = (
                self._internal_clock - self._playing_start_time
            ) * self.rate
        elif self._state == PAUSED:
            # If paused, then draw the frame that was playing at the time the
            # SurfaceAnimation object was paused
            elapsed = (
                self._paused_start_time - self._playing_start_time
            ) * self.rate
        if self._loop:
            elapsed = elapsed % self.duration
        else:
            elapsed = clip(elapsed, 0, self.duration)
        elapsed += 0.00001  # done to compensate for rounding errors
        return elapsed

    @elapsed.setter
    def elapsed(self, elapsed: float) -> None:
        # NOTE: Do to floating point rounding errors, this doesn't work
        # precisely.
        elapsed += 0.00001  # done to compensate for rounding errors
        # TODO - I really need to find a better way to handle the floating
        # point thing.

        # Set the elapsed time to a specific value.
        if self._loop:
            elapsed = elapsed % self.duration
        else:
            elapsed = clip(elapsed, 0, self.duration)

        rightNow = self._internal_clock
        self._playing_start_time = rightNow - (elapsed * self.rate)

        if self.state in (PAUSED, STOPPED):
            self.state = PAUSED  # if stopped, then set to paused
            self._paused_start_time = rightNow

    @property
    def progress(self) -> float:
        """Get the progress of the animation."""
        if self.duration == 0:
            return 0
        return self.elapsed / self.duration

    @property
    def frames_played(self) -> int:
        """Get the number of frames that have been played."""
        return bisect.bisect(self._start_times, self.elapsed) - 1

    @frames_played.setter
    def frames_played(self, frame_num: int) -> None:
        """Change the elapsed time to the beginning of a specific frame."""
        if self.loop:
            frame_num = frame_num % len(self._images)
        else:
            frame_num = clip(frame_num, 0, len(self._images) - 1)
        self.elapsed = self._start_times[frame_num]

    @property
    def frames_remaining(self) -> int:
        """Get the number of frames remaining to be played."""
        return len(self._images) - self.frames_played - 1

    @property
    def duration(self) -> float:
        """Get the total duration of the animation."""
        return self._start_times[-1]


class SurfaceAnimationCollection:
    def __init__(
        self,
        *animations: Union[
            SurfaceAnimation,
            Sequence[SurfaceAnimation],
            Mapping[Any, SurfaceAnimation],
        ],
    ) -> None:
        self._animations: list[SurfaceAnimation] = []
        self.add(*animations)
        self._state: State = STOPPED

    def add(
        self,
        *animations: Union[
            SurfaceAnimation,
            Sequence[SurfaceAnimation],
            Mapping[Any, SurfaceAnimation],
        ],
    ) -> None:
        for animation in animations:
            if isinstance(animation, SurfaceAnimation):
                self._animations.append(animation)
            elif isinstance(animation, Sequence):
                self._animations.extend(animation)
            elif isinstance(animation, Mapping):
                self._animations.extend(animation.values())
            else:
                raise ValueError("Invalid animation type")

    def remove(self, animation: SurfaceAnimation) -> None:
        self._animations.remove(animation)

    def clear(self) -> None:
        self._animations.clear()

    @property
    def animations(self) -> Sequence[SurfaceAnimation]:
        return self._animations

    @property
    def state(self) -> State:
        if self.is_finished():
            self._state = STOPPED

        return self._state

    def is_finished(self) -> bool:
        return all(a.is_finished() for a in self._animations)

    def play(self, start_time: Optional[float] = None) -> None:
        for anim_obj in self._animations:
            anim_obj.play(start_time)

        self._state = PLAYING

    def pause(self, start_time: Optional[float] = None) -> None:
        for anim_obj in self._animations:
            anim_obj.pause(start_time)

        self._state = PAUSED

    def stop(self) -> None:
        for anim_obj in self._animations:
            anim_obj.stop()
        self._state = STOPPED

    def update(self, time_delta: float) -> None:
        """
        Update the internal clock with the elapsed time.

        Parameters:
            time_delta: Time elapsed since last call to update.

        """
        for anim_obj in self._animations:
            anim_obj.update(time_delta)


T = TypeVar("T", bound=float)


def clip(value: T, lower: T, upper: T) -> T:
    """Clip value to [lower, upper] range."""
    return lower if value < lower else upper if value > upper else value
