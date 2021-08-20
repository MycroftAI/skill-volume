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

from mycroft.util import LOG

from .alsa import AlsaHAL

class Mark1HAL(AlsaHAL):
    """Emulate the Hardware Abstraction Layer (HAL) for the Mark 1.

    This class will be deprecated at the earliest possible moment.
    """
    def __init__(self, settings):
        super().__init__(settings)
        self._enclosure = EnclosureAPI(self.bus, self.__class__.__name__)

    def _show_volume(self, volume):
        """Perform any hardware based display of volume level."""
        level = round(volume / 10)  # convert % to int(0..10)
        self._enclosure.eyes_volume(new_level)
        pass
