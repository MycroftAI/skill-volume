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
from mycroft.messagebus.message import Message
from mycroft.util import LOG, start_message_bus_client

class HAL():
    """Emulate the Hardware Abstraction Layer (HAL) for audio.

    This class will be deprecated at the earliest possible moment.

    Terminology:
       "Level" =  Mycroft volume levels, from 0 to 10
       "Volume" = ALSA mixer setting, from 0 to 100
    """
    def __init__(self, settings):
        self.default_volume = settings.get('default_volume', 60)
        self.min_volume = settings.get('min_volume', 0)
        self.max_volume = settings.get('max_volume', 83)
        self.volume_step = (self.max_volume - self.min_volume) / 10
        self.vol_before_mute = None

        self.bus = MessageBusClient()
        self.register_volume_control_handlers()
        start_message_bus_client('AUDIO_HAL', self.bus)
    
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

    def _show_volume(self):
        """Perform any hardware based display of volume level."""
        pass

    def _set_default_volume(self, message):
        self.default_volume = message.data['default_volume']

    def _decrease_volume(self, message):
        """Decrease the volume by 10%."""
        current_volume = self._get_volume()
        target_volume = current_volume - self.volume_step
        request_data = {'percent': target_volume / 100}
        response = self._set_volume(Message('mycroft.volume.set', data=request_data))
        if response['success']:
            self.bus.emit(message.reply('mycroft.volume.decrease.response', 
                                    data=response))

    def _increase_volume(self, message):
        """Increase the volume by 10%."""
        current_volume = self._get_volume()
        target_volume = current_volume + self.volume_step
        request_data = {'percent': target_volume / 100}
        response = self._set_volume(Message('mycroft.volume.set', data=request_data))
        if response['success']:
            self.bus.emit(message.reply('mycroft.volume.increased', data=response))

    def _mute_volume(self, message):
        """Mute the audio output."""
        self.volume_before_mute = self._get_volume()
        LOG.debug('Muting. Volume before mute: {}'.format(self.volume_before_mute))
        self._set_volume(Message('mycroft.volume.set',
                                 data={'percentage': 0}))
        self.bus.emit(message.reply('mycroft.volume.muted', data={'success': true}))
    
    def _unmute_volume(self, message):
        """Unmute the audio output returning to previous volume level."""
        LOG.debug('Unmuting to volume before mute: {}'.format(self.volume_before_mute))
        request_data = {'percentage': self.volume_before_mute / 100}
        response = self.bus.wait_for_response(Message('mycroft.volume.set', 
                                                      data=request_data))
        if response and response.data['success']:
            self.bus.emit(message.reply('mycroft.volume.unmuted', 
                                    data=response.data))

    def _duck(self, message):
        """Temporarily duck (significantly lower) audio output."""
        if self.settings.get('ducking', True):
            self._mute_volume()

    def _unduck(self, message):
        """Restore audio output volume after ducking."""
        pass

    def constrain_volume(self, target_volume):
        """Ensure volume is within the min and max values."""
        if target_volume > self.max_volume:
            settable_volume = self.max_volume
        elif target_volume < self.min_volume:
            settable_volume = self.min_volume
        else:
            settable_volume = target_volume
        return settable_volume
