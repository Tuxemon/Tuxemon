# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from abc import ABC, abstractmethod
from ctypes import Structure, Union, c_int, cdll, pointer
from threading import Lock
from typing import Any

from tuxemon.rumble.tools import RumbleParams

logger = logging.getLogger(__name__)

Shake_EffectType = c_int
SHAKE_EFFECT_RUMBLE = Shake_EffectType(0)
SHAKE_EFFECT_PERIODIC = Shake_EffectType(1)
SHAKE_EFFECT_CONSTANT = Shake_EffectType(2)
SHAKE_EFFECT_SPRING = Shake_EffectType(3)
SHAKE_EFFECT_FRICTION = Shake_EffectType(4)
SHAKE_EFFECT_DAMPER = Shake_EffectType(5)
SHAKE_EFFECT_INERTIA = Shake_EffectType(6)
SHAKE_EFFECT_RAMP = Shake_EffectType(7)
SHAKE_EFFECT_COUNT = Shake_EffectType(8)

Shake_PeriodicWaveform = c_int
SHAKE_PERIODIC_SQUARE = Shake_PeriodicWaveform(0)
SHAKE_PERIODIC_TRIANGLE = Shake_PeriodicWaveform(1)
SHAKE_PERIODIC_SINE = Shake_PeriodicWaveform(2)
SHAKE_PERIODIC_SAW_UP = Shake_PeriodicWaveform(3)
SHAKE_PERIODIC_SAW_DOWN = Shake_PeriodicWaveform(4)
SHAKE_PERIODIC_CUSTOM = Shake_PeriodicWaveform(5)
SHAKE_PERIODIC_COUNT = Shake_PeriodicWaveform(6)


class Shake_EffectRumble(Structure):
    _fields_ = [("strongMagnitude", c_int), ("weakMagnitude", c_int)]


class Shake_Envelope(Structure):
    _fields_ = [
        ("attackLength", c_int),
        ("attackLevel", c_int),
        ("fadeLength", c_int),
        ("fadeLevel", c_int),
    ]


class Shake_EffectPeriodic(Structure):
    _fields_ = [
        ("waveform", Shake_PeriodicWaveform),
        ("period", c_int),
        ("magnitude", c_int),
        ("offset", c_int),
        ("phase", c_int),
        ("envelope", Shake_Envelope),
    ]


class Shake_Union(Union):
    _fields_ = [
        ("rumble", Shake_EffectRumble),
        ("periodic", Shake_EffectPeriodic),
    ]


class Shake_Effect(Structure):
    _anonymous_ = "u"
    _fields_ = [
        ("type", Shake_EffectType),
        ("id", c_int),
        ("direction", c_int),
        ("length", c_int),
        ("delay", c_int),
        ("u", Shake_Union),
    ]


class Rumble(ABC):
    @abstractmethod
    def rumble(self, params: RumbleParams) -> None:
        """Start or simulate a rumble effect on the controller."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update internal state, clean up expired effects, etc."""

    @abstractmethod
    def rumble_sequence(
        self, target: int, sequence: list[tuple[float, float]]
    ) -> None:
        """Play a sequence of rumble effects on a device."""


class DummyRumble(Rumble):
    def __init__(self) -> None:
        logger.info(
            "DummyRumble initialized. No hardware effects will be played."
        )

    def rumble(self, params: RumbleParams) -> None:
        logger.debug(f"[DummyRumble] rumble called with {params}")

    def update(self, dt: float) -> None:
        pass

    def rumble_sequence(
        self, target: int, sequence: list[tuple[float, float]]
    ) -> None:
        logger.debug(
            f"[DummyRumble] rumble_sequence called on target {target} with {sequence}"
        )

    def device_info(self, device: Any) -> None:
        logger.info(
            f"[DummyRumble] Device info requested for {device}. Returning dummy values."
        )

    def device_count(self) -> int:
        return 0

    def quit(self) -> None:
        logger.info("[DummyRumble] Quit called. Nothing to clean up.")


class LibShakeRumble(Rumble):
    def __init__(self, library: str = "libshake.so") -> None:
        try:
            self.libShake = cdll.LoadLibrary(library)
            self.libShake.Shake_Init()
        except OSError as e:
            raise RuntimeError(f"Failed to load library '{library}': {e}")

        self.effect_type = SHAKE_EFFECT_PERIODIC
        self.periodic_waveform = SHAKE_PERIODIC_SINE
        self.lock = Lock()
        self._elapsed_time: float = 0.0
        self._active_effects: dict[int, list[dict[str, Any]]] = {}

    def rumble(self, params: RumbleParams) -> None:
        """
        Start the rumble effect for the given target device(s).
        """

        def create_and_start_effect(target_device: int) -> None:
            device = self.libShake.Shake_Open(target_device)
            if device < 0:
                logger.warning(f"Failed to open device {target_device}.")
                return

            with self.lock:
                effect = Shake_Effect()
                self.libShake.Shake_InitEffect(
                    pointer(effect), self.effect_type
                )

                # configure effect fields...
                effect.periodic.waveform = self.periodic_waveform
                effect.periodic.period = int(params.period)
                effect.periodic.magnitude = int(params.magnitude)
                effect.periodic.envelope.attackLength = int(
                    params.attack_length
                )
                effect.periodic.envelope.attackLevel = int(params.attack_level)
                effect.periodic.envelope.fadeLength = int(params.fade_length)
                effect.periodic.envelope.fadeLevel = int(params.fade_level)

                effect.direction = int(params.direction)
                effect.length = int(params.length * 1000)
                effect.delay = int(params.delay)

                id = self.libShake.Shake_UploadEffect(device, pointer(effect))
                if id < 0:
                    logger.warning("Failed to upload effect.")
                    self.libShake.Shake_Close(device)
                    return

                self.libShake.Shake_Play(device, id)

                end_time = self._elapsed_time + params.length
                effect_record = {"id": id, "end_time": end_time}

                # append to list instead of overwriting
                if device not in self._active_effects:
                    self._active_effects[device] = []
                self._active_effects[device].append(effect_record)

        if params.target == -1:
            for i in range(self.libShake.Shake_NumOfDevices()):
                create_and_start_effect(i)
        else:
            create_and_start_effect(int(params.target))

    def update(self, dt: float) -> None:
        self._elapsed_time += dt
        with self.lock:
            for device, effects in list(self._active_effects.items()):
                expired = []
                for effect_info in effects:
                    if self._elapsed_time >= effect_info["end_time"]:
                        self.libShake.Shake_EraseEffect(
                            device, effect_info["id"]
                        )
                        expired.append(effect_info)
                # remove expired effects
                for e in expired:
                    effects.remove(e)
                # if no effects left, close device and remove entry
                if not effects:
                    self.libShake.Shake_Close(device)
                    del self._active_effects[device]

    def device_info(self, device: Any) -> None:
        """
        Retrieve information about a device. Optionally print or log the details.

        Parameters:
            device: The target device.
        """
        info = {
            "id": self.libShake.Shake_DeviceId(device),
            "name": self.libShake.Shake_DeviceName(device),
            "gain_support": self.libShake.Shake_QueryGainSupport(device),
            "autocenter_support": self.libShake.Shake_QueryAutocenterSupport(
                device
            ),
            "effect_capacity": self.libShake.Shake_DeviceEffectCapacity(
                device
            ),
            "supported_effects": [],
        }

        # Add supported effects
        effect_types = [
            ("SHAKE_EFFECT_RUMBLE", SHAKE_EFFECT_RUMBLE),
            ("SHAKE_EFFECT_PERIODIC", SHAKE_EFFECT_PERIODIC),
            ("SHAKE_EFFECT_CONSTANT", SHAKE_EFFECT_CONSTANT),
            ("SHAKE_EFFECT_SPRING", SHAKE_EFFECT_SPRING),
            ("SHAKE_EFFECT_FRICTION", SHAKE_EFFECT_FRICTION),
            ("SHAKE_EFFECT_DAMPER", SHAKE_EFFECT_DAMPER),
            ("SHAKE_EFFECT_INERTIA", SHAKE_EFFECT_INERTIA),
            ("SHAKE_EFFECT_RAMP", SHAKE_EFFECT_RAMP),
        ]
        waveforms = [
            ("SHAKE_PERIODIC_SQUARE", SHAKE_PERIODIC_SQUARE),
            ("SHAKE_PERIODIC_TRIANGLE", SHAKE_PERIODIC_TRIANGLE),
            ("SHAKE_PERIODIC_SINE", SHAKE_PERIODIC_SINE),
            ("SHAKE_PERIODIC_SAW_UP", SHAKE_PERIODIC_SAW_UP),
            ("SHAKE_PERIODIC_SAW_DOWN", SHAKE_PERIODIC_SAW_DOWN),
            ("SHAKE_PERIODIC_CUSTOM", SHAKE_PERIODIC_CUSTOM),
        ]

        for name, effect in effect_types:
            if self.libShake.Shake_QueryEffectSupport(device, effect):
                info["supported_effects"].append(name)
                if effect == SHAKE_EFFECT_PERIODIC:
                    for waveform_name, waveform in waveforms:
                        if self.libShake.Shake_QueryWaveformSupport(
                            device, waveform
                        ):
                            info["supported_effects"].append(
                                f"* {waveform_name}"
                            )

        logger.info(f"Device #{info['id']}")
        logger.info(f" Name: {info['name']}")
        logger.info(f" Adjustable gain: {info['gain_support']}")
        logger.info(f" Adjustable autocenter: {info['autocenter_support']}")
        logger.info(f" Effect capacity: {info['effect_capacity']}")
        logger.info(" Supported effects:")
        for effect in info["supported_effects"]:
            logger.info(f"  {effect}")

    def device_count(self) -> int:
        """Return the number of available devices."""
        return int(self.libShake.Shake_NumOfDevices())

    def quit(self) -> None:
        """Clean up and release resources."""
        with self.lock:
            for device, effects in self._active_effects.items():
                for effect_info in effects:
                    self.libShake.Shake_EraseEffect(device, effect_info["id"])
                self.libShake.Shake_Close(device)
            self._active_effects.clear()
        self.libShake.Shake_Quit()

    def rumble_sequence(
        self, target: int, sequence: list[tuple[float, float]]
    ) -> None:
        """
        Play a sequence of rumble effects on a device.

        Parameters:
            target: Device index (or -1 for all devices).
            sequence: List of (duration, pause) tuples in seconds.
                    Example: [(0.2, 0.1), (0.2, 0.1), (0.2, 0.0)]
                    → rumble 0.2s, pause 0.1s, rumble 0.2s, pause 0.1s, rumble 0.2s
        """

        def create_effect(
            device: int, duration: float, pause: float, start_time: float
        ) -> float:
            effect = Shake_Effect()
            self.libShake.Shake_InitEffect(pointer(effect), self.effect_type)

            # Configure periodic waveform for pulsation
            effect.periodic.waveform = self.periodic_waveform
            effect.periodic.period = 200  # ms cycle length
            effect.periodic.magnitude = 20000
            effect.periodic.envelope.attackLength = 50
            effect.periodic.envelope.attackLevel = 0
            effect.periodic.envelope.fadeLength = 50
            effect.periodic.envelope.fadeLevel = 0

            effect.direction = 0
            effect.length = int(duration * 1000)  # ms
            effect.delay = int(pause * 1000)  # ms

            id = self.libShake.Shake_UploadEffect(device, pointer(effect))
            if id < 0:
                logger.warning("Failed to upload effect.")
                return start_time

            self.libShake.Shake_Play(device, id)

            end_time = start_time + duration + pause
            if device not in self._active_effects:
                self._active_effects[device] = []
            self._active_effects[device].append(
                {"id": id, "end_time": end_time}
            )

            return end_time

        if target == -1:
            devices = list(range(self.libShake.Shake_NumOfDevices()))
        else:
            devices = [target]

        for device in devices:
            handle = self.libShake.Shake_Open(device)
            if handle < 0:
                logger.warning(f"Failed to open device {device}.")
                continue

            with self.lock:
                start_time = self._elapsed_time
                for duration, pause in sequence:
                    start_time = create_effect(
                        handle, duration, pause, start_time
                    )
