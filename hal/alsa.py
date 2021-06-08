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

from alsaaudio import Mixer, mixers as alsa_mixers

from mycroft.util import LOG

def get_alsa_mixer(self):
    LOG.debug('Finding Alsa Mixer for control...')
    mixer = None
    try:
        # If there are only 1 mixer use that one
        mixers = alsa_mixers()
        if len(mixers) == 1:
            mixer = Mixer(mixers[0])
        elif 'Master' in mixers:
            # Try using the default mixer (Master)
            mixer = Mixer('Master')
        elif 'PCM' in mixers:
            # PCM is another common one
            mixer = Mixer('PCM')
        elif 'Digital' in mixers:
            # My mixer is called 'Digital' (JustBoom DAC)
            mixer = Mixer('Digital')
        else:
            # should be equivalent to 'Master'
            mixer = Mixer()
    except Exception:
        # Retry instanciating the mixer with the built-in default
        try:
            mixer = Mixer()
        except Exception as e:
            LOG.error('Couldn\'t allocate mixer, {}'.format(repr(e)))
    return mixer