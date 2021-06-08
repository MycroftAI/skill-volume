# Copyright 2021 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Provides access to the ALSA audio system.

DEPRECATION NOTICE: 
This will shortly be moved out of the Volume Skill to the Hardware Abstraction
Layer (HAL). The Volume Skill will be emitting messages to the bus, and the
HAL will be responsible for managing the system state.
"""

from mycroft.messagebus.client import MessageBusClient
from mycroft.util import LOG, start_message_bus_client

class HAL():
    """Emulate the Hardware Abstraction Layer (HAL) for audio.

    This class will be deprecated at the earliest possible moment.
    """
    def __init__(self):
        self.bus = MessageBusClient()
        self.register_volume_control_handlers()
        start_message_bus_client("AUDIO_HAL", self.bus)
    
    def register_volume_control_handlers(self):
        self.bus.on('mycroft.volume.get', self._get_volume)
        self.bus.on('mycroft.volume.set', self._set_volume)
        self.bus.on('mycroft.volume.increase', self._increase_volume)
        self.bus.on('mycroft.volume.decrease', self._decrease_volume)
        self.bus.on('mycroft.volume.mute', self._mute_volume)
        self.bus.on('mycroft.volume.unmute', self._unmute_volume)
        self.bus.on('recognizer_loop:record_begin', self._duck)
        self.bus.on('recognizer_loop:record_end', self._unduck)

    def _get_volume(self, message):
        """Get the current volume level."""
        pass

    def _set_volume(self, message):
        """Set the volume level."""
        pass

    def _decrease_volume(self, message):
        """Decrease the volume by 10%."""
        pass

    def _increase_volume(self, message):
        """Increase the volume by 10%."""
        pass

    def _mute_volume(self, message):
        """Mute the audio output."""
        pass
    
    def _unmute_volume(self, message):
        """Unmute the audio output returning to previous volume level."""
        pass

    def _duck(self, message):
        """Temporarily duck (significantly lower) audio output."""
        pass

    def _unduck(self, message):
        """Restore audio output volume after ducking."""
        pass
