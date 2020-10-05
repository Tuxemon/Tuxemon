from ctypes import *
from threading import Thread
from time import sleep

from tuxemon.core.rumble.tools import Rumble

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
    _fields_ = [
        ("strongMagnitude", c_int),
        ("weakMagnitude", c_int)]

class Shake_Envelope(Structure):
    _fields_ = [
        ("attackLength", c_int),
        ("attackLevel", c_int),
        ("fadeLength", c_int),
        ("fadeLevel", c_int)]

class Shake_EffectPeriodic(Structure):
    _fields_ = [
        ("waveform", Shake_PeriodicWaveform),
        ("period", c_int),
        ("magnitude", c_int),
        ("offset", c_int),
        ("phase", c_int),
        ("envelope", Shake_Envelope)]

class Shake_Union(Union):
    _fields_ = [
        ("rumble", Shake_EffectRumble),
        ("periodic", Shake_EffectPeriodic)]

class Shake_Effect(Structure):
    _anonymous_ = ('u')
    _fields_ = [
        ("type", Shake_EffectType),
        ("id", c_int),
        ("direction", c_int),
        ("length", c_int),
        ("delay", c_int),
        ("u", Shake_Union)]

class LibShakeRumble(Rumble):
    def __init__(self, library='libshake.so'):
        self.libShake = cdll.LoadLibrary(library)
        self.libShake.Shake_Init()
        self.effect_type = SHAKE_EFFECT_PERIODIC
        self.periodic_waveform = SHAKE_PERIODIC_SINE

    def rumble(self, target=0, period=25, magnitude=24576, length=2, delay=0,
            attack_length=256, attack_level=0, fade_length=256, fade_level=0,
            direction=16384):
        # Target -1 will target all available devices
        if target == -1:
            for i in range(self.libShake.Shake_NumOfDevices()):
                self._start_thread(i, period, magnitude, length, delay, attack_length,
                                   attack_level, fade_length, fade_level, direction)
        else:
            self._start_thread(target, period, magnitude, length, delay, attack_length,
                               attack_level, fade_length, fade_level, direction)

    def _rumble_thread(self, target=0, period=25, magnitude=24576, length=2, delay=0,
            attack_length=256, attack_level=0, fade_length=256, fade_level=0,
            direction=16384):
        if self.libShake.Shake_NumOfDevices() > 0:
            device = self.libShake.Shake_Open(target)

            effect = Shake_Effect()
            self.libShake.Shake_InitEffect(pointer(effect), self.effect_type)
            if self.effect_type == SHAKE_EFFECT_PERIODIC:
                effect.periodic.waveform               = self.periodic_waveform
                effect.periodic.period                 = period
                effect.periodic.magnitude              = magnitude
                effect.periodic.envelope.attackLengeth = attack_length
                effect.periodic.envelope.attackLevel   = attack_level
                effect.periodic.envelope.fadeLength    = fade_length
                effect.periodic.envelope.fadeLevel     = fade_level
            effect.direction                       = direction
            effect.length                          = int(length * 1000)
            effect.delay                           = delay

            id = self.libShake.Shake_UploadEffect(device, pointer(effect))
            self.libShake.Shake_Play(device, id)

            sleep(length)
            self.libShake.Shake_EraseEffect(device, id)
            self.libShake.Shake_Close(device)

    def _start_thread(self, target=0, period=25, magnitude=24576, length=2, delay=0,
            attack_length=256, attack_level=0, fade_length=256, fade_level=0,
            direction=16384):
        t = Thread(target=self._rumble_thread,
                   args=(target, period, magnitude, length, delay, attack_length,
                         attack_level, fade_length, fade_level, direction))
        t.daemon = True
        t.start()

    def device_info(self, device):
        print("Device #%d" % self.libShake.Shake_DeviceId(device))
        print(" Name:", self.libShake.Shake_DeviceName(device))
        print(" Adjustable gain:", self.libShake.Shake_QueryGainSupport(device))
        print(" Adjustable autocenter:", self.libShake.Shake_QueryAutocenterSupport(device))
        print(" Effect capacity:", self.libShake.Shake_DeviceEffectCapacity(device))
        print(" Supported effects:")
        if self.libShake.Shake_QueryEffectSupport(device, SHAKE_EFFECT_RUMBLE):
            print("  SHAKE_EFFECT_RUMBLE")

        if self.libShake.Shake_QueryEffectSupport(device, SHAKE_EFFECT_PERIODIC):
            print("  SHAKE_EFFECT_PERIODIC")
            if self.libShake.Shake_QueryWaveformSupport(device, SHAKE_PERIODIC_SQUARE):
                print("  * SHAKE_PERIODIC_SQUARE")
            if self.libShake.Shake_QueryWaveformSupport(device, SHAKE_PERIODIC_TRIANGLE):
                print("  * SHAKE_PERIODIC_TRIANGLE")
            if self.libShake.Shake_QueryWaveformSupport(device, SHAKE_PERIODIC_SINE):
                print("  * SHAKE_PERIODIC_SINE")
            if self.libShake.Shake_QueryWaveformSupport(device, SHAKE_PERIODIC_SAW_UP):
                print("  * SHAKE_PERIODIC_SAW_UP")
            if self.libShake.Shake_QueryWaveformSupport(device, SHAKE_PERIODIC_SAW_DOWN):
                print("  * SHAKE_PERIODIC_SAW_DOWN")
            if self.libShake.Shake_QueryWaveformSupport(device, SHAKE_PERIODIC_CUSTOM):
                print("  * SHAKE_PERIODIC_CUSTOM")

        if self.libShake.Shake_QueryEffectSupport(device, SHAKE_EFFECT_CONSTANT):
            print("  SHAKE_EFFECT_CONSTANT")
        if self.libShake.Shake_QueryEffectSupport(device, SHAKE_EFFECT_SPRING):
            print("  SHAKE_EFFECT_SPRING")
        if self.libShake.Shake_QueryEffectSupport(device, SHAKE_EFFECT_FRICTION):
            print("  SHAKE_EFFECT_FRICTION")
        if self.libShake.Shake_QueryEffectSupport(device, SHAKE_EFFECT_DAMPER):
            print("  SHAKE_EFFECT_DAMPER")
        if self.libShake.Shake_QueryEffectSupport(device, SHAKE_EFFECT_INERTIA):
            print("  SHAKE_EFFECT_INERTIA")
        if self.libShake.Shake_QueryEffectSupport(device, SHAKE_EFFECT_RAMP):
            print("  SHAKE_EFFECT_RAMP")

    def device_count(self):
        return self.libShake.Shake_NumOfDevices()

    def quit(self):
        self.libShake.Shake_Quit()


