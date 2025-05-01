# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from ctypes import *
from threading import Lock, Thread
from time import sleep
from typing import Any

from tuxemon.rumble.tools import Rumble, RumbleParams

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

    def rumble(self, params: RumbleParams) -> None:
        """
        Start the rumble effect for the given target device(s).
        """
        if params.target == -1:  # Target all devices
            for i in range(self.libShake.Shake_NumOfDevices()):
                params.target = i
                self._start_thread(params)
        else:
            self._start_thread(params)

    def _execute_rumble_effect(self, params: RumbleParams) -> None:
        """
        Execute the rumble effect on the target device.
        """
        if self.libShake.Shake_NumOfDevices() > 0:
            device = self.libShake.Shake_Open(int(params.target))

            with self.lock:
                effect = Shake_Effect()
                self.libShake.Shake_InitEffect(
                    pointer(effect), self.effect_type
                )

                if self.effect_type == SHAKE_EFFECT_PERIODIC:
                    effect.periodic.waveform = self.periodic_waveform
                    effect.periodic.period = int(params.period)
                    effect.periodic.magnitude = int(params.magnitude)
                    effect.periodic.envelope.attackLength = int(
                        params.attack_length
                    )
                    effect.periodic.envelope.attackLevel = int(
                        params.attack_level
                    )
                    effect.periodic.envelope.fadeLength = int(
                        params.fade_length
                    )
                    effect.periodic.envelope.fadeLevel = int(params.fade_level)

                effect.direction = int(params.direction)
                effect.length = int(
                    params.length * 1000
                )  # Convert to milliseconds
                effect.delay = int(params.delay)

                id = self.libShake.Shake_UploadEffect(device, pointer(effect))
                self.libShake.Shake_Play(device, id)

                sleep(params.length)  # Wait for the duration of the effect
                self.libShake.Shake_EraseEffect(device, id)

            self.libShake.Shake_Close(device)

    def _start_thread(self, params: RumbleParams) -> None:
        """
        Start a thread to execute the rumble effect.
        """
        t = Thread(target=self._execute_rumble_effect, args=(params,))
        t.daemon = True
        t.start()

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

        print(f"Device #{info['id']}")
        print(f" Name: {info['name']}")
        print(f" Adjustable gain: {info['gain_support']}")
        print(f" Adjustable autocenter: {info['autocenter_support']}")
        print(f" Effect capacity: {info['effect_capacity']}")
        print(" Supported effects:")
        for effect in info["supported_effects"]:
            print(f"  {effect}")

    def device_count(self) -> int:
        """Return the number of available devices."""
        return int(self.libShake.Shake_NumOfDevices())

    def quit(self) -> None:
        """Clean up and release resources."""
        self.libShake.Shake_Quit()
