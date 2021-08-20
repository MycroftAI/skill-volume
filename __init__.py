# Copyright 2017 Mycroft AI Inc.
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
from os.path import dirname, join

from adapt.intent import IntentBuilder
from mycroft.audio import wait_while_speaking
from mycroft.messagebus.message import Message
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util import play_wav
from mycroft.util.parse import extract_number

from .hal import HALFactory


ALSA_PLATFORMS = ['mycroft_mark_1', 'picroft', 'unknown']


class VolumeSkill(MycroftSkill):
    """
    Control the audio volume for the Mycroft system

    Terminology:
       "Level" =  Mycroft volume levels, from 0 to 10
       "Volume" = ALSA mixer setting, from 0 to 100
    """

    MIN_LEVEL = 0
    MAX_LEVEL = 10

    # TODO: Translation layer (have to match word in Level.voc)
    VOLUME_WORDS = {
        'loud': 9,
        'normal': 6,
        'quiet': 3
    }

    def __init__(self):
        super(VolumeSkill, self).__init__("VolumeSkill")
        self.settings["default_level"] = 6  # can be 0 (off) to 10 (max)
        self.settings["min_volume"] = 0     # can be 0 to 100
        if self.config_core['enclosure'].get('platform') == 'mycroft_mark_1':
            self.settings["max_volume"] = 83   # can be 0 to 83
        else:
            self.settings["max_volume"] = 100   # can be 0 to 100
        self.volume_sound = join(dirname(__file__), "blop-mark-diangelo.wav")
        # Instantiate the HAL emulator
        self.platform = self.config_core['enclosure'].get('platform', 'unknown')
        if self.platform in ALSA_PLATFORMS:
            self.HAL = HALFactory.create('ALSA', self.settings)
        else:
            self.HAL = None    

    def initialize(self):
        # Register handlers to detect percentages as reported by STT
        for i in range(101):  # numbers 0 to 100
            self.register_vocabulary(str(i) + '%', 'Percent')

    def _set_volume(self, vol, emit=True):
        self.bus.emit(Message('mycroft.volume.set',
                                data={"percent": vol/100.0}))

    # Change Volume to X (Number 0 to) Intent Handlers
    @intent_handler(IntentBuilder("SetVolume").require("Volume")
                    .optionally("Increase").optionally("Decrease")
                    .optionally("To").require("Level"))
    def handle_set_volume(self, message):
        default_vol = self.__get_system_volume(50)

        level = self.__get_volume_level(message, default_vol)
        self._set_volume(self.__level_to_volume(level))
        if level == self.MAX_LEVEL:
            self.speak_dialog('max.volume')
        else:
            self.speak_dialog('set.volume', data={'volume': level})

    # Set Volume Percent Intent Handlers
    @intent_handler(IntentBuilder("SetVolumePercent").require("Volume")
                    .optionally("Increase").optionally("Decrease")
                    .optionally("To").require("Percent"))
    def handle_set_volume_percent(self, message):
        percent = extract_number(message.data['utterance'].replace('%', ''))
        percent = int(percent)
        self._set_volume(percent)
        self.speak_dialog('set.volume.percent', data={'level': percent})

    # Volume Status Intent Handlers
    @intent_handler(IntentBuilder("QueryVolume").optionally("Query")
                    .require("Volume"))
    def handle_query_volume(self, message):
        level = self.__volume_to_level(self.__get_system_volume(0, show=True))
        self.speak_dialog('volume.is', data={'volume': round(level)})

    @intent_handler(IntentBuilder("QueryVolumePhrase").require("QueryPhrase")
                    .optionally("Volume"))
    def handle_query_volume_phrase(self, message):
        self.handle_query_volume(message)

    def __communicate_volume_change(self, message, dialog, code, changed):
        play_sound = message.data.get('play_sound', False)
        if play_sound:
            if changed:
                play_wav(self.volume_sound)
        else:
            if (not changed) and (code != 0):
                self.speak_dialog('already.max.volume', data={'volume': code})

    # Increase Volume Intent Handlers
    @intent_handler(IntentBuilder("IncreaseVolume").require("Volume")
                    .require("Increase"))
    def handle_increase_volume(self, message):
        self.__communicate_volume_change(message, 'increase.volume',
                                         *self.__update_volume(+1))

    @intent_handler(IntentBuilder("IncreaseVolumeSet").require("Set")
                    .optionally("Volume").require("Increase"))
    def handle_increase_volume_set(self, message):
        self.handle_increase_volume(message)

    @intent_handler(IntentBuilder("IncreaseVolumePhrase")
                    .require("IncreasePhrase"))
    def handle_increase_volume_phrase(self, message):
        self.handle_increase_volume(message)

    # Decrease Volume Intent Handlers
    @intent_handler(IntentBuilder("DecreaseVolume").require("Volume")
                    .require("Decrease"))
    def handle_decrease_volume(self, message):
        self.log.info("DECREASING VOLUME")
        response = self.bus.wait_for_response(Message('mycroft.volume.decrease'))
        self.log.error(response)
        if response and response.data['success']:
            self.speak_dialog('decrease.volume', response.data)
        # self.__communicate_volume_change(message, 'decrease.volume',
                                        #  *self.__update_volume(-1))

    @intent_handler(IntentBuilder("DecreaseVolumeSet").require("Set")
                    .optionally("Volume").require("Decrease"))
    def handle_decrease_volume_set(self, message):
        self.handle_decrease_volume(message)

    @intent_handler(IntentBuilder("DecreaseVolumePhrase")
                    .require("DecreasePhrase"))
    def handle_decrease_volume_phrase(self, message):
        self.handle_decrease_volume(message)

    # Maximum Volume Intent Handlers
    @intent_handler(IntentBuilder("MaxVolume").optionally("Set")
                    .require("Volume").optionally("Increase")
                    .require("MaxVolume"))
    def handle_max_volume(self, message):
        self._set_volume(self.settings["max_volume"])
        speak_message = message.data.get('speak_message', True)
        if speak_message:
            self.speak_dialog('max.volume')
            wait_while_speaking()
        self.bus.emit(Message('mycroft.volume.duck'))

    @intent_handler(IntentBuilder("MaxVolumeIncreaseMax")
                    .require("MaxVolumePhrase").optionally("Volume")
                    .require("Increase").optionally("MaxVolume"))
    def handle_max_volume_increase_to_max(self, message):
        self.handle_max_volume(message)

    def duck(self, message):
        if self.settings.get('ducking', True):
            self._mute_volume()

    def unduck(self, message):
        if self.settings.get('ducking', True):
            self._unmute_volume()

    def _mute_volume(self, message=None, speak=False):
        if speak:
            self.speak_dialog('mute.volume')
            wait_while_speaking()
        self.bus.emit(Message('mycroft.volume.mute'))

    # Mute Volume Intent Handlers
    @intent_handler(IntentBuilder("MuteVolume").require(
        "Volume").require("Mute"))
    def handle_mute_volume(self, message):
        self._mute_volume(speak=message.data.get('speak_message', True))

    def _unmute_volume(self, message=None, speak=False):
        self.bus.emit(Message('mycroft.volume.unmute'))
        if speak:
            self.speak_dialog('reset.volume',
                              data={'volume':
                                    self.settings["default_level"]})

    # Unmute/Reset Volume Intent Handlers
    @intent_handler(IntentBuilder("UnmuteVolume").require("Volume")
                    .require("Unmute"))
    def handle_unmute_volume(self, message):
        self._unmute_volume(speak=message.data.get('speak_message', True))

    def __volume_to_level(self, volume):
        """
            Convert a 'volume' to a 'level'

            Args:
                volume (int): min_volume..max_volume
            Returns:
                int: the equivalent level
        """
        range = self.MAX_LEVEL - self.MIN_LEVEL
        min_vol = self.settings["min_volume"]
        max_vol = self.settings["max_volume"]
        prop = float(volume - min_vol) / max_vol
        level = int(round(self.MIN_LEVEL + range * prop))
        if level > self.MAX_LEVEL:
            level = self.MAX_LEVEL
        elif level < self.MIN_LEVEL:
            level = self.MIN_LEVEL
        return level

    def __level_to_volume(self, level):
        """
            Convert a 'level' to a 'volume'

            Args:
                level (int): 0..MAX_LEVEL
            Returns:
                int: the equivalent volume
        """
        range = self.settings["max_volume"] - self.settings["min_volume"]
        prop = float(level) / self.MAX_LEVEL
        volume = int(round(self.settings["min_volume"] + int(range) * prop))

        return volume

    @staticmethod
    def __bound_level(level):
        if level > VolumeSkill.MAX_LEVEL:
            level = VolumeSkill.MAX_LEVEL
        elif level < VolumeSkill.MIN_LEVEL:
            level = VolumeSkill.MIN_LEVEL
        return level

    def __update_volume(self, change=0):
        """
            Attempt to change audio level

            Args:
                change (int): +1 or -1; the step to change by

            Returns: tuple(new level code int(0..10),
                           whether level changed (bool))
        """
        old_level = self.__volume_to_level(self.__get_system_volume(0))
        new_level = self.__bound_level(old_level + change)
        self.enclosure.eyes_volume(new_level)
        self._set_volume(self.__level_to_volume(new_level))
        return new_level, new_level != old_level

    def __get_system_volume(self, default=50, show=False):
        """Get volume from message bus.

        The show parameter should only be True when a user is requesting
        the volume and not the system.
        """
        vol = default
        vol_msg = self.bus.wait_for_response(
                            Message("mycroft.volume.get", {'show': show}))
        if vol_msg:
            vol = int(vol_msg.data["percent"] * 100)

        return vol

    def __get_volume_level(self, message, default=None):
        """ Retrieves volume from message. """
        level_str = str(message.data.get('Level', default))
        level = self.settings["default_level"]

        try:
            level = self.VOLUME_WORDS[level_str]
        except KeyError:
            try:
                level = int(extract_number(level_str))
                if (level == self.MAX_LEVEL + 1):
                    # Assume that user meant max volume
                    level = self.MAX_LEVEL
                elif (level > self.MAX_LEVEL):
                    # Guess that the user said something like 100 percent
                    # so convert that into a level value
                    level = self.MAX_LEVEL * level/100
            except ValueError:
                pass

        level = self.__bound_level(level)
        return level


def create_skill():
    return VolumeSkill()
