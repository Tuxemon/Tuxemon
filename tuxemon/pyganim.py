#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# pyganim A sprite animation module for Pygame.
#
# Pyganim (pyganim.py, ver 1)
#
#
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pyganim
# Released under a "Simplified BSD" license
#
# There's a tutorial (and sample code) on how to use this library at http://inventwithpython.com/pyganim
# NOTE: This module requires Pygame to be installed to use. Download it from http://pygame.org
#
# This should be compatible with both Python 2 and Python 3. Please email any
# bug reports to Al at al@inventwithpython.com
#


# TODO: Feature idea: if the same image file is specified, re-use the Surface object.
# (Make this optional though.)
from __future__ import annotations
import time

import pygame

# setting up constants
from pygame.rect import Rect
from typing import Union, Literal, Sequence, Tuple, Optional, Any, Final, List,\
    TypeVar, Mapping
import bisect

PLAYING: Final = "playing"
PAUSED: Final = "paused"
STOPPED: Final = "stopped"

State = Literal["playing", "paused", "stopped"]


class PygAnimation:
    def __init__(
        self,
        frames: Union[
            Literal["_copy"],
            Sequence[Tuple[Union[str, pygame.surface.Surface], float]]
        ],
        loop: bool = True,
    ) -> None:
        # Constructor function for the animation object. Starts off in the STOPPED state.
        #
        # @param frames
        #     A list of tuples for each frame of animation, in one of the following format:
        #       (image_of_frame<pygame.Surface>, duration_in_seconds<int>)
        #       (filename_of_image<str>, duration_in_seconds<int>)
        #     Note that the images and duration cannot be changed. A new PygAnimation object
        #     will have to be created.
        # @param loop Tells the animation object to keep playing in a loop.

        # _images stores the pygame.Surface objects of each frame
        self._images = []
        # _durations stores the durations (in seconds) of each frame.
        # e.g. [1, 1, 2.5] means the first and second frames last one second,
        # and the third frame lasts for two and half seconds.
        self._durations = []
        # _startTimes shows when each frame begins. len(self._startTimes) will
        # always be one more than len(self._images), because the last number
        # will be when the last frame ends, rather than when it starts.
        # The values are in seconds.
        # So self._startTimes[-1] tells you the length of the entire animation.
        # e.g. if _durations is [1, 1, 2.5], then _startTimes will be [0, 1, 2, 4.5]

        # if the sprites are transformed, the originals are kept in _images
        # and the transformed sprites are kept in _transformedImages.
        self._transformedImages: List[pygame.surface.Surface] = []

        self._state: State = STOPPED  # The state is always either PLAYING, PAUSED, or STOPPED
        self._loop = loop  # If True, the animation will keep looping. If False, the animation stops after playing once.
        self._rate = 1.0  # 2.0 means play the animation twice as fast, 0.5 means twice as slow
        self._visibility = True  # If False, then nothing is drawn when the blit() methods are called

        self._playingStartTime = 0.0  # the time that the play() function was last called.
        self._pausedStartTime = 0.0  # the time that the pause() function was last called.

        self.numFrames = len(frames)
        assert self.numFrames > 0, "Must contain at least one frame."
        for i in range(self.numFrames):
            # load each frame of animation into _images
            frame = frames[i]
            assert type(frame) in (list, tuple) and len(frame) == 2, "Frame %s has incorrect format." % (i)
            assert type(frame[0]) in (
                str,
                pygame.Surface,
            ), "Frame %s image must be a string filename or a pygame.Surface" % (i)
            assert frame[1] > 0, "Frame %s duration must be greater than zero." % (i)
            frame_img = pygame.image.load(frame[0]) if isinstance(frame[0], str) else frame[0]
            self._images.append(frame_img)
            self._durations.append(frame[1])
        self._startTimes = self._getStartTimes()

    def _getStartTimes(self) -> Sequence[float]:
        # Internal method to get the start times based off of the _durations list.
        # Don't call this method.
        startTimes = [0.0]
        for i in range(self.numFrames):
            startTimes.append(startTimes[-1] + self._durations[i])
        return startTimes

    def blit(
        self,
        destSurface: pygame.surface.Surface,
        dest: pygame.rect.Rect,
    ) -> None:
        # Draws the appropriate frame of the animation to the destination Surface
        # at the specified position.
        #
        # NOTE: If the visibility attribute is False, then nothing will be drawn.
        #
        # @param destSurface
        #     The Surface object to draw the frame
        # @param dest
        #     The position to draw the frame. This is passed to Pygame's Surface's
        #     blit() function, so it can be either a (top, left) tuple or a Rect
        #     object.
        if self.isFinished():
            self.state = STOPPED
        if not self.visibility or self.state == STOPPED:
            return
        destSurface.blit(self.getCurrentFrame(), dest)

    def getFrame(self, frameNum: int) -> pygame.surface.Surface:
        # Returns the pygame.Surface object of the frameNum-th frame in this
        # animation object. If there is a transformed version of the frame,
        # it will return that one.
        if self._transformedImages == []:
            return self._images[frameNum]
        else:
            return self._transformedImages[frameNum]

    def getCurrentFrame(self) -> pygame.surface.Surface:
        # Returns the pygame.Surface object of the frame that would be drawn
        # if the blit() method were called right now. If there is a transformed
        # version of the frame, it will return that one.
        return self.getFrame(self.currentFrameNum)

    def isFinished(self) -> bool:
        # Returns True if this animation doesn't loop and has finished playing
        # all the frames it has.
        return not self.loop and self.elapsed >= self._startTimes[-1]

    def play(self, startTime: Optional[float] = None) -> None:
        # Start playing the animation.

        # play() is essentially a setter function for self._state
        # NOTE: Don't adjust the self.state property, only self._state

        if startTime is None:
            startTime = time.time()

        if self._state == PLAYING:
            if self.isFinished():
                # if the animation doesn't loop and has already finished, then
                # calling play() causes it to replay from the beginning.
                self._playingStartTime = startTime
        elif self._state == STOPPED:
            # if animation was stopped, start playing from the beginning
            self._playingStartTime = startTime
        elif self._state == PAUSED:
            # if animation was paused, start playing from where it was paused
            self._playingStartTime = startTime - (self._pausedStartTime - self._playingStartTime)
        self._state = PLAYING

    def pause(self, startTime: Optional[float] = None) -> None:
        # Stop having the animation progress, and keep it at the current frame.

        # pause() is essentially a setter function for self._state
        # NOTE: Don't adjust the self.state property, only self._state

        if startTime is None:
            startTime = time.time()

        if self._state == PAUSED:
            return  # do nothing
        elif self._state == PLAYING:
            self._pausedStartTime = startTime
        elif self._state == STOPPED:
            rightNow = time.time()
            self._playingStartTime = rightNow
            self._pausedStartTime = rightNow
        self._state = PAUSED

    def stop(self) -> None:
        # Reset the animation to the beginning frame, and do not continue playing

        # stop() is essentially a setter function for self._state
        # NOTE: Don't adjust the self.state property, only self._state
        if self._state == STOPPED:
            return  # do nothing
        self._state = STOPPED

    def getMaxSize(self) -> Tuple[int, int]:
        # Goes through all the Surface objects in this animation object
        # and returns the max width and max height that it finds. (These
        # widths and heights may be on different Surface objects.)
        frameWidths = []
        frameHeights = []
        for i in range(len(self._images)):
            frameWidth, frameHeight = self._images[i].get_size()
            frameWidths.append(frameWidth)
            frameHeights.append(frameHeight)
        maxWidth = max(frameWidths)
        maxHeight = max(frameHeights)

        return (maxWidth, maxHeight)

    def get_rect(self) -> pygame.rect.Rect:
        # Returns a Rect object for this animation object.
        # The top and left will be set to 0, 0, and the width and height
        # will be set to what is returned by getMaxSize().
        maxWidth, maxHeight = self.getMaxSize()
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
            # if we are turning off looping while the animation is playing,
            # we need to modify the _playingStartTime so that the rest of
            # the animation will play, and then stop. (Otherwise, the
            # animation will immediately stop playing if it has already looped.)
            self._playingStartTime = time.time() - self.elapsed
        self._loop = bool(loop)

    @property
    def state(self) -> State:
        if self.isFinished():
            self._state = STOPPED  # if finished playing, then set state to STOPPED.

        return self._state

    @state.setter
    def state(self, state: State) -> None:
        if state not in (PLAYING, PAUSED, STOPPED):
            raise ValueError("state must be one of pyganim.PLAYING, pyganim.PAUSED, or pyganim.STOPPED")
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
        # NOTE: Do to floating point rounding errors, this doesn't work precisely.

        # To prevent infinite recursion, don't use the self.state property,
        # just read/set self._state directly because the state getter calls
        # this method.

        # Find out how long ago the play()/pause() functions were called.
        if self._state == STOPPED:
            # if stopped, then just return 0
            return 0

        if self._state == PLAYING:
            # if playing, then draw the current frame (based on when the animation
            # started playing). If not looping and the animation has gone through
            # all the frames already, then draw the last frame.
            elapsed = (time.time() - self._playingStartTime) * self.rate
        elif self._state == PAUSED:
            # if paused, then draw the frame that was playing at the time the
            # PygAnimation object was paused
            elapsed = (self._pausedStartTime - self._playingStartTime) * self.rate
        if self._loop:
            elapsed = elapsed % self._startTimes[-1]
        else:
            elapsed = clip(elapsed, 0, self._startTimes[-1])
        elapsed += 0.00001  # done to compensate for rounding errors
        return elapsed

    @elapsed.setter
    def elapsed(self, elapsed: float) -> None:
        # NOTE: Do to floating point rounding errors, this doesn't work precisely.
        elapsed += 0.00001  # done to compensate for rounding errors
        # TODO - I really need to find a better way to handle the floating point thing.

        # Set the elapsed time to a specific value.
        if self._loop:
            elapsed = elapsed % self._startTimes[-1]
        else:
            elapsed = clip(elapsed, 0, self._startTimes[-1])

        rightNow = time.time()
        self._playingStartTime = rightNow - (elapsed * self.rate)

        if self.state in (PAUSED, STOPPED):
            self.state = PAUSED  # if stopped, then set to paused
            self._pausedStartTime = rightNow

    @property
    def currentFrameNum(self) -> int:
        # Return the frame number of the frame that will be currently
        # displayed if the animation object were drawn right now.
        return bisect.bisect(self._startTimes, self.elapsed) - 1

    @currentFrameNum.setter
    def currentFrameNum(self, frameNum: int) -> None:
        # Change the elapsed time to the beginning of a specific frame.
        if self.loop:
            frameNum = frameNum % len(self._images)
        else:
            frameNum = clip(frameNum, 0, len(self._images) - 1)
        self.elapsed = self._startTimes[frameNum]


class PygConductor:
    def __init__(
        self,
        *animations: Union[
            PygAnimation,
            Sequence[PygAnimation],
            Mapping[Any, PygAnimation],
        ],
    ) -> None:
        self._animations: List[PygAnimation] = []
        if animations:
            self.add(*animations)
        self._state: State = STOPPED

    def add(
        self,
        *animations: Union[
            PygAnimation,
            Sequence[PygAnimation],
            Mapping[Any, PygAnimation],
        ],
    ) -> None:
        if isinstance(animations[0], Mapping):
            for k in animations[0].keys():
                self._animations.append(animations[0][k])
        elif isinstance(animations[0], Sequence):
            for i in range(len(animations[0])):
                self._animations.append(animations[0][i])
        else:
            for i in range(len(animations)):
                anim = animations[i]
                assert isinstance(anim, PygAnimation)
                self._animations.append(anim)

    @property
    def animations(self) -> Sequence[PygAnimation]:
        return self._animations

    @animations.setter
    def animations(self, val: List[PygAnimation]) -> None:
        self._animations = val

    @property
    def state(self) -> State:
        if self.isFinished():
            self._state = STOPPED

        return self._state

    def isFinished(self) -> bool:
        result = all(a.isFinished() for a in self._animations)
        return result

    def play(self, startTime: Optional[float] = None) -> None:
        if startTime is None:
            startTime = time.time()

        for animObj in self._animations:
            animObj.play(startTime)

        self._state = PLAYING

    def pause(self, startTime: Optional[float] = None) -> None:
        if startTime is None:
            startTime = time.time()

        for animObj in self._animations:
            animObj.pause(startTime)

        self._state = PAUSED

    def stop(self) -> None:
        for animObj in self._animations:
            animObj.stop()
        self._state = STOPPED


T = TypeVar("T", bound=float)


def clip(value: T, lower: T, upper: T) -> T:
    """Clip value to [lower, upper] range."""
    return lower if value < lower else upper if value > upper else value
