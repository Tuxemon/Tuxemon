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

PLAYING: Final = "playing"
PAUSED: Final = "paused"
STOPPED: Final = "stopped"

State = Literal["playing", "paused", "stopped"]

# These values are used in the anchor() method.
NORTHWEST: Final = "northwest"
NORTH: Final = "north"
NORTHEAST: Final = "northeast"
WEST: Final = "west"
CENTER: Final = "center"
EAST: Final = "east"
SOUTHWEST: Final = "southwest"
SOUTH: Final = "south"
SOUTHEAST: Final = "southeast"

Anchor = Literal[
    "northwest",
    "north",
    "northeast",
    "west",
    "center",
    "east",
    "southwest",
    "south",
    "southeast",
]


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

        if frames != "_copy":  # ('_copy' is passed for frames by the getCopies() method)
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

    def reverse(self) -> None:
        # Reverses the order of the animations.
        self.elapsed = self._startTimes[-1] - self.elapsed
        self._images.reverse()
        self._transformedImages.reverse()
        self._durations.reverse()

    def getCopy(self) -> PygAnimation:
        # Returns a copy of this PygAnimation object, but one that refers to the
        # Surface objects of the original so it efficiently uses memory.
        #
        # NOTE: Messing around with the original Surface objects will affect all
        # the copies. If you want to modify the Surface objects, then just make
        # copies using constructor function instead.
        return self.getCopies(1)[0]

    def getCopies(self, numCopies: int = 1) -> Sequence[PygAnimation]:
        # Returns a list of copies of this PygAnimation object, but one that refers to the
        # Surface objects of the original so it efficiently uses memory.
        #
        # NOTE: Messing around with the original Surface objects will affect all
        # the copies. If you want to modify the Surface objects, then just make
        # copies using constructor function instead.
        retval = []
        for i in range(numCopies):
            newAnim = PygAnimation("_copy", loop=self.loop)
            newAnim._images = self._images[:]
            newAnim._transformedImages = self._transformedImages[:]
            newAnim._durations = self._durations[:]
            newAnim._startTimes = self._startTimes[:]
            newAnim.numFrames = self.numFrames
            retval.append(newAnim)
        return retval

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
        frameNum = findStartTime(self._startTimes, self.elapsed)
        destSurface.blit(self.getFrame(frameNum), dest)

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

    def clearTransforms(self) -> None:
        # Deletes all the transformed frames so that the animation object
        # displays the original Surfaces/images as they were before
        # transformation functions were called on them.
        #
        # This is handy to do for multiple transformation, where calling
        # the rotation or scaling functions multiple times results in
        # degraded/noisy images.
        self._transformedImages = []

    def makeTransformsPermanent(self) -> None:
        self._images = [pygame.Surface(surfObj.get_size(), 0, surfObj) for surfObj in self._transformedImages]
        for i in range(len(self._transformedImages)):
            self._images[i].blit(self._transformedImages[i], (0, 0))

    def blitFrameNum(
        self,
        frameNum: int,
        destSurface: pygame.surface.Surface,
        dest: pygame.rect.Rect,
    ) -> None:
        # Draws the specified frame of the animation object. This ignores the
        # current playing state.
        #
        # NOTE: If the visibility attribute is False, then nothing will be drawn.
        #
        # @param frameNum
        #     The frame to draw (the first frame is 0, not 1)
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
        destSurface.blit(self.getFrame(frameNum), dest)

    def blitFrameAtTime(
        self,
        elapsed: float,
        destSurface: pygame.surface.Surface,
        dest: pygame.rect.Rect,
    ) -> None:
        # Draws the frame the is "elapsed" number of seconds into the animation,
        # rather than the time the animation actually started playing.
        #
        # NOTE: If the visibility attribute is False, then nothing will be drawn.
        #
        # @param elapsed
        #     The amount of time into an animation to use when determining which
        #     frame to draw. blitFrameAtTime() uses this parameter rather than
        #     the actual time that the animation started playing. (In seconds)
        # @param destSurface
        #     The Surface object to draw the frame
        # @param dest
        #     The position to draw the frame. This is passed to Pygame's Surface's
        #     blit() function, so it can be either a (top, left) tuple or a Rect
        #     object.        elapsed = int(elapsed * self.rate)
        if self.isFinished():
            self.state = STOPPED
        if not self.visibility or self.state == STOPPED:
            return
        frameNum = findStartTime(self._startTimes, elapsed)
        destSurface.blit(self.getFrame(frameNum), dest)

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

    def togglePause(self) -> None:
        # If paused, start playing. If playing, then pause.

        # togglePause() is essentially a setter function for self._state
        # NOTE: Don't adjust the self.state property, only self._state

        if self._state == PLAYING:
            if self.isFinished():
                # the one exception: if this animation doesn't loop and it
                # has finished playing, then toggling the pause will cause
                # the animation to replay from the beginning.
                # self._playingStartTime = time.time() # effectively the same as calling play()
                self.play()
            else:
                self.pause()
        elif self._state in (PAUSED, STOPPED):
            self.play()

    def areFramesSameSize(self) -> bool:
        # Returns True if all the Surface objects in this animation object
        # have the same width and height. Otherwise, returns False
        width, height = self.getFrame(0).get_size()
        for i in range(len(self._images)):
            if self.getFrame(i).get_size() != (width, height):
                return False
        return True

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

    def anchor(self, anchorPoint: Anchor = "northwest") -> None:
        # If the Surface objects are of different sizes, align them all to a
        # specific "anchor point" (one of the NORTH, SOUTH, SOUTHEAST, etc. constants)
        #
        # By default, they are all anchored to the NORTHWEST corner.
        if self.areFramesSameSize():
            return  # nothing needs to be anchored
            # This check also prevents additional calls to anchor() from doing
            # anything, since anchor() sets all the image to the same size.
            # The lesson is, you can only effectively call anchor() once.

        self.clearTransforms()  # clears transforms since this method anchors the original images.

        maxWidth, maxHeight = self.getMaxSize()
        halfMaxWidth = int(maxWidth / 2)
        halfMaxHeight = int(maxHeight / 2)

        for i in range(len(self._images)):
            # go through and copy all frames to a max-sized Surface object
            # NOTE: This makes changes to the original images in self._images, not the transformed images in self._transformedImages
            newSurf = pygame.Surface(
                (maxWidth, maxHeight)
            )  # TODO: this is probably going to have errors since I'm using the default depth.

            # set the expanded areas to be transparent
            newSurf = newSurf.convert_alpha()
            newSurf.fill((0, 0, 0, 0))

            frameWidth, frameHeight = self._images[i].get_size()
            halfFrameWidth = int(frameWidth / 2)
            halfFrameHeight = int(frameHeight / 2)

            # position the Surface objects to the specified anchor point
            if anchorPoint == NORTHWEST:
                newSurf.blit(self._images[i], (0, 0))
            elif anchorPoint == NORTH:
                newSurf.blit(self._images[i], (halfMaxWidth - halfFrameWidth, 0))
            elif anchorPoint == NORTHEAST:
                newSurf.blit(self._images[i], (maxWidth - frameWidth, 0))
            elif anchorPoint == WEST:
                newSurf.blit(self._images[i], (0, halfMaxHeight - halfFrameHeight))
            elif anchorPoint == CENTER:
                newSurf.blit(self._images[i], (halfMaxWidth - halfFrameWidth, halfMaxHeight - halfFrameHeight))
            elif anchorPoint == EAST:
                newSurf.blit(self._images[i], (maxWidth - frameWidth, halfMaxHeight - halfFrameHeight))
            elif anchorPoint == SOUTHWEST:
                newSurf.blit(self._images[i], (0, maxHeight - frameHeight))
            elif anchorPoint == SOUTH:
                newSurf.blit(self._images[i], (halfMaxWidth - halfFrameWidth, maxHeight - frameHeight))
            elif anchorPoint == SOUTHEAST:
                newSurf.blit(self._images[i], (maxWidth - frameWidth, maxHeight - frameHeight))
            self._images[i] = newSurf

    def nextFrame(self, jump: int = 1) -> None:
        # Set the elapsed time to the beginning of the next frame.
        # You can jump ahead by multiple frames by specifying a different
        # argument for jump.
        # Negative values have the same effect as calling prevFrame()
        self.currentFrameNum += int(jump)

    def prevFrame(self, jump: int = 1) -> None:
        # Set the elapsed time to the beginning of the previous frame.
        # You can jump ahead by multiple frames by specifying a different
        # argument for jump.
        # Negative values have the same effect as calling nextFrame()
        self.currentFrameNum -= int(jump)

    def rewind(self, seconds: Optional[float] = None) -> None:
        # Set the elapsed time back relative to the current elapsed time.
        if seconds is None:
            self.elapsed = 0.0
        else:
            self.elapsed -= seconds

    def fastForward(self, seconds: Optional[float] = None) -> None:
        # Set the elapsed time forward relative to the current elapsed time.
        if seconds is None:
            self.elapsed = self._startTimes[-1] - 0.00002  # done to compensate for rounding errors
        else:
            self.elapsed += seconds

    def _makeTransformedSurfacesIfNeeded(self) -> None:
        # Internal-method. Creates the Surface objects for the _transformedImages list.
        # Don't call this method.
        if self._transformedImages == []:
            self._transformedImages = [surf.copy() for surf in self._images]

    # Transformation methods.
    # (These are analogous to the pygame.transform.* functions, except they
    # are applied to all frames of the animation object.
    def flip(self, xbool: bool, ybool: bool) -> None:
        # Flips the image horizontally, vertically, or both.
        # See http://pygame.org/docs/ref/transform.html#pygame.transform.flip
        self._makeTransformedSurfacesIfNeeded()
        for i in range(len(self._images)):
            self._transformedImages[i] = pygame.transform.flip(self.getFrame(i), xbool, ybool)

    def scale(self, width_height: Tuple[float, float]) -> None:
        # NOTE: Does not support the DestSurface parameter
        # Increases or decreases the size of the images.
        # See http://pygame.org/docs/ref/transform.html#pygame.transform.scale
        self._makeTransformedSurfacesIfNeeded()
        for i in range(len(self._images)):
            self._transformedImages[i] = pygame.transform.scale(self.getFrame(i), width_height)

    def rotate(self, angle: float) -> None:
        # Rotates the image.
        # See http://pygame.org/docs/ref/transform.html#pygame.transform.rotate
        self._makeTransformedSurfacesIfNeeded()
        for i in range(len(self._images)):
            self._transformedImages[i] = pygame.transform.rotate(self.getFrame(i), angle)

    def rotozoom(self, angle: float, scale: float) -> None:
        # Rotates and scales the image simultaneously.
        # See http://pygame.org/docs/ref/transform.html#pygame.transform.rotozoom
        self._makeTransformedSurfacesIfNeeded()
        for i in range(len(self._images)):
            self._transformedImages[i] = pygame.transform.rotozoom(self.getFrame(i), angle, scale)

    def scale2x(self) -> None:
        # NOTE: Does not support the DestSurface parameter
        # Double the size of the image using an efficient algorithm.
        # See http://pygame.org/docs/ref/transform.html#pygame.transform.scale2x
        self._makeTransformedSurfacesIfNeeded()
        for i in range(len(self._images)):
            self._transformedImages[i] = pygame.transform.scale2x(self.getFrame(i))

    def smoothscale(self, width_height: Tuple[float, float]) -> None:
        # NOTE: Does not support the DestSurface parameter
        # Scales the image smoothly. (Computationally more expensive and
        # slower but produces a better scaled image.)
        # See http://pygame.org/docs/ref/transform.html#pygame.transform.smoothscale
        self._makeTransformedSurfacesIfNeeded()
        for i in range(len(self._images)):
            self._transformedImages[i] = pygame.transform.smoothscale(self.getFrame(i), width_height)

    # pygame.Surface method wrappers
    # These wrappers call their analogous pygame.Surface methods on all Surface objects in this animation.
    # They are here for the convenience of the module user. These calls will apply to the transform images,
    # and can have their effects undone by called clearTransforms()
    #
    # It is not advisable to call these methods on the individual Surface objects in self._images.
    def _surfaceMethodWrapper(self, wrappedMethodName: str, *args: Any, **kwargs: Any) -> None:
        self._makeTransformedSurfacesIfNeeded()
        for i in range(len(self._images)):
            methodToCall = getattr(self._transformedImages[i], wrappedMethodName)
            methodToCall(*args, **kwargs)

    # There's probably a more terse way to generate the following methods,
    # but I don't want to make the code even more unreadable.
    def convert(self, *args: Any, **kwargs: Any) -> None:
        # See http://pygame.org/docs/ref/surface.html#Surface.convert
        self._surfaceMethodWrapper("convert", *args, **kwargs)

    def convert_alpha(self, *args: Any, **kwargs: Any) -> None:
        # See http://pygame.org/docs/ref/surface.html#Surface.convert_alpha
        self._surfaceMethodWrapper("convert_alpha", *args, **kwargs)

    def set_alpha(self, *args: Any, **kwargs: Any) -> None:
        # See http://pygame.org/docs/ref/surface.html#Surface.set_alpha
        self._surfaceMethodWrapper("set_alpha", *args, **kwargs)

    def scroll(self, *args: Any, **kwargs: Any) -> None:
        # See http://pygame.org/docs/ref/surface.html#Surface.scroll
        self._surfaceMethodWrapper("scroll", *args, **kwargs)

    def set_clip(self, *args: Any, **kwargs: Any) -> None:
        # See http://pygame.org/docs/ref/surface.html#Surface.set_clip
        self._surfaceMethodWrapper("set_clip", *args, **kwargs)

    def set_colorkey(self, *args: Any, **kwargs: Any) -> None:
        # See http://pygame.org/docs/ref/surface.html#Surface.set_colorkey
        self._surfaceMethodWrapper("set_colorkey", *args, **kwargs)

    def lock(self, *args: Any, **kwargs: Any) -> None:
        # See http://pygame.org/docs/ref/surface.html#Surface.unlock
        self._surfaceMethodWrapper("lock", *args, **kwargs)

    def unlock(self, *args: Any, **kwargs: Any) -> None:
        # See http://pygame.org/docs/ref/surface.html#Surface.lock
        self._surfaceMethodWrapper("unlock", *args, **kwargs)

    # Getter and setter methods for properties
    def _propGetRate(self) -> float:
        return self._rate

    def _propSetRate(self, rate: float) -> None:
        rate = float(rate)
        if rate < 0:
            raise ValueError("rate must be greater than 0.")
        self._rate = rate

    rate = property(_propGetRate, _propSetRate)

    def _propGetLoop(self) -> bool:
        return self._loop

    def _propSetLoop(self, loop: bool) -> None:
        if self.state == PLAYING and self._loop and not loop:
            # if we are turning off looping while the animation is playing,
            # we need to modify the _playingStartTime so that the rest of
            # the animation will play, and then stop. (Otherwise, the
            # animation will immediately stop playing if it has already looped.)
            self._playingStartTime = time.time() - self.elapsed
        self._loop = bool(loop)

    loop = property(_propGetLoop, _propSetLoop)

    def _propGetState(self) -> State:
        if self.isFinished():
            self._state = STOPPED  # if finished playing, then set state to STOPPED.

        return self._state

    def _propSetState(self, state: State) -> None:
        if state not in (PLAYING, PAUSED, STOPPED):
            raise ValueError("state must be one of pyganim.PLAYING, pyganim.PAUSED, or pyganim.STOPPED")
        if state == PLAYING:
            self.play()
        elif state == PAUSED:
            self.pause()
        elif state == STOPPED:
            self.stop()

    state = property(_propGetState, _propSetState)

    def _propGetVisibility(self) -> bool:
        return self._visibility

    def _propSetVisibility(self, visibility: bool) -> None:
        self._visibility = bool(visibility)

    visibility = property(_propGetVisibility, _propSetVisibility)

    def _propSetElapsed(self, elapsed: float) -> None:
        # NOTE: Do to floating point rounding errors, this doesn't work precisely.
        elapsed += 0.00001  # done to compensate for rounding errors
        # TODO - I really need to find a better way to handle the floating point thing.

        # Set the elapsed time to a specific value.
        if self._loop:
            elapsed = elapsed % self._startTimes[-1]
        else:
            elapsed = getInBetweenValue(0, elapsed, self._startTimes[-1])

        rightNow = time.time()
        self._playingStartTime = rightNow - (elapsed * self.rate)

        if self.state in (PAUSED, STOPPED):
            self.state = PAUSED  # if stopped, then set to paused
            self._pausedStartTime = rightNow

    def _propGetElapsed(self) -> float:
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
            elapsed = getInBetweenValue(0, elapsed, self._startTimes[-1])
        elapsed += 0.00001  # done to compensate for rounding errors
        return elapsed

    elapsed = property(_propGetElapsed, _propSetElapsed)

    def _propGetCurrentFrameNum(self) -> int:
        # Return the frame number of the frame that will be currently
        # displayed if the animation object were drawn right now.
        return findStartTime(self._startTimes, self.elapsed)

    def _propSetCurrentFrameNum(self, frameNum: int) -> None:
        # Change the elapsed time to the beginning of a specific frame.
        if self.loop:
            frameNum = frameNum % len(self._images)
        else:
            frameNum = getInBetweenValue(0, frameNum, len(self._images) - 1)
        self.elapsed = self._startTimes[frameNum]

    currentFrameNum = property(_propGetCurrentFrameNum, _propSetCurrentFrameNum)


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

    def _propGetAnimations(self) -> Sequence[PygAnimation]:
        return self._animations

    def _propSetAnimations(self, val: List[PygAnimation]) -> None:
        self._animations = val

    animations = property(_propGetAnimations, _propSetAnimations)

    def _propGetState(self) -> State:
        if self.isFinished():
            self._state = STOPPED

        return self._state

    def isFinished(self) -> bool:
        result = all(a.isFinished() for a in self._animations)
        return result

    def isStopped(self) -> bool:
        return self._state == STOPPED

    state = property(_propGetState)

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

    def reverse(self) -> None:
        for animObj in self._animations:
            animObj.reverse()

    def clearTransforms(self) -> None:
        for animObj in self._animations:
            animObj.clearTransforms()

    def makeTransformsPermanent(self) -> None:
        for animObj in self._animations:
            animObj.makeTransformsPermanent()

    def togglePause(self) -> None:
        for animObj in self._animations:
            animObj.togglePause()

    def nextFrame(self, jump: int = 1) -> None:
        for animObj in self._animations:
            animObj.nextFrame(jump)

    def prevFrame(self, jump: int = 1) -> None:
        for animObj in self._animations:
            animObj.prevFrame(jump)

    def rewind(self, seconds: Optional[float] = None) -> None:
        for animObj in self._animations:
            animObj.rewind(seconds)

    def fastForward(self, seconds: Optional[float] = None) -> None:
        for animObj in self._animations:
            animObj.fastForward(seconds)

    def flip(self, xbool: bool, ybool: bool) -> None:
        for animObj in self._animations:
            animObj.flip(xbool, ybool)

    def scale(self, width_height: Tuple[float, float]) -> None:
        for animObj in self._animations:
            animObj.scale(width_height)

    def rotate(self, angle: float) -> None:
        for animObj in self._animations:
            animObj.rotate(angle)

    def rotozoom(self, angle: float, scale: float) -> None:
        for animObj in self._animations:
            animObj.rotozoom(angle, scale)

    def scale2x(self) -> None:
        for animObj in self._animations:
            animObj.scale2x()

    def smoothscale(self, width_height: Tuple[float, float]) -> None:
        for animObj in self._animations:
            animObj.smoothscale(width_height)

    def convert(self) -> None:
        for animObj in self._animations:
            animObj.convert()

    def convert_alpha(self) -> None:
        for animObj in self._animations:
            animObj.convert_alpha()

    def set_alpha(self, *args: Any, **kwargs: Any) -> None:
        for animObj in self._animations:
            animObj.set_alpha(*args, **kwargs)

    def scroll(self, dx: int = 0, dy: int = 0) -> None:
        for animObj in self._animations:
            animObj.scroll(dx, dy)

    def set_clip(self, *args: Any, **kwargs: Any) -> None:
        for animObj in self._animations:
            animObj.set_clip(*args, **kwargs)

    def set_colorkey(self, *args: Any, **kwargs: Any) -> None:
        for animObj in self._animations:
            animObj.set_colorkey(*args, **kwargs)

    def lock(self) -> None:
        for animObj in self._animations:
            animObj.lock()

    def unlock(self) -> None:
        for animObj in self._animations:
            animObj.unlock()


T = TypeVar("T", bound=float)

def getInBetweenValue(lowerBound: T, value: T, upperBound: T) -> T:
    # Returns the value within the bounds of the lower and upper bound parameters.
    # If value is less than lowerBound, then return lowerBound.
    # If value is greater than upperBound, then return upperBound.
    # Otherwise, just return value as it is.
    if value < lowerBound:
        return lowerBound
    elif value > upperBound:
        return upperBound
    return value


def findStartTime(startTimes: Sequence[float], target: float) -> int:
    # With startTimes as a list of sequential numbers and target as a number,
    # returns the index of the number in startTimes that preceeds target.
    #
    # For example, if startTimes was [0, 2, 4.5, 7.3, 10] and target was 6,
    # then findStartTime() would return 2. If target was 12, returns 4.
    assert startTimes[0] == 0
    lb = 0  # "lb" is lower bound
    ub = len(startTimes) - 1  # "ub" is upper bound

    # handle special cases:
    if not startTimes:
        return 0
    if target >= startTimes[-1]:
        return ub - 1

    # perform binary search:
    while True:
        i = int((ub - lb) / 2) + lb

        if startTimes[i] == target or (startTimes[i] < target and startTimes[i + 1] > target):
            if i == len(startTimes):
                return i - 1
            else:
                return i

        if startTimes[i] < target:
            lb = i
        elif startTimes[i] > target:
            ub = i
