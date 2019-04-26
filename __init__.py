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
import time
from alsaaudio import Mixer, mixers as alsa_mixers
from os.path import dirname, join

from adapt.intent import IntentBuilder
from mycroft.audio import wait_while_speaking
from mycroft.messagebus.message import Message
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util import play_wav
from mycroft.util.parse import extract_number


class VolumeSkill(MycroftSkill):
    """
    Control the audio volume for the Mycroft system

    Terminology:
       "Level" =  Mycroft volume levels, from 0 to 11
       "Volume" = ALSA mixer setting, from 0 to 100
    """

    MIN_LEVEL = 0
    MAX_LEVEL = 11

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
        try:
            # If there are only 1 mixer use that one
            mixers = alsa_mixers()
            if len(mixers) == 1:
                self.mixer = Mixer(mixers[0])
            else:  # Try using the default mixer
                self.mixer = Mixer()
        except Exception:
            # Retry instanciating the mixer
            try:
                self.mixer = Mixer()
            except Exception as e:
                self.log.error('Couldn\'t allocate mixer, {}'.format(repr(e)))

    def initialize(self):
        # Register handlers to detect percentages as reported by STT
        for i in range(101): # numbers 0 to 100
            self.register_vocabulary(str(i) + '%', 'Percent')

        # Register handlers for messagebus events
        self.add_event('mycroft.volume.increase',
                       self.handle_increase_volume)
        self.add_event('mycroft.volume.decrease',
                       self.handle_decrease_volume)
        self.add_event('mycroft.volume.mute',
                       self.handle_mute_volume)
        self.add_event('mycroft.volume.unmute',
                       self.handle_unmute_volume)

    def _setvolume(self, vol, emit=True):
        # Update ALSA
        self.mixer.setvolume(vol)
        # TODO: Remove this and control volume at the Enclosure level in
        # response to the mycroft.volume.set message.

        if emit:
            # Notify non-ALSA systems of volume change
            self.bus.emit(Message('mycroft.volume.set',
                                  data={"percent": vol/100.0}))

    @intent_handler(IntentBuilder("SetVolume").require(
        "Volume").require("Level"))
    def handle_set_volume(self, message):
        level = self.__get_volume_level(message, self.mixer.getvolume()[0])
        self._setvolume(self.__level_to_volume(level))
        self.speak_dialog('set.volume', data={'volume': level})

    @intent_handler(IntentBuilder("SetVolumePercent").require(
        "Volume").require("Percent"))
    def handle_set_volume_percent(self, message):
        percent = extract_number(message.data['utterance'].replace('%', ''))
        percent = int(percent)
        self._setvolume(percent)
        self.speak_dialog('set.volume.percent', data={'level': percent})

    @intent_handler(IntentBuilder("QueryVolume").require(
        "Volume").require("Query"))
    def handle_query_volume(self, message):
        level = self.__volume_to_level(self.mixer.getvolume()[0])
        self.speak_dialog('volume.is', data={'volume': round(level)})

    def __communicate_volume_change(self, message, dialog, code, changed):
        play_sound = message.data.get('play_sound', False)
        if play_sound:
            if changed:
                play_wav(self.volume_sound)
        else:
            if not changed:
                dialog = 'already.max.volume'
            self.speak_dialog(dialog, data={'volume': code})

    @intent_handler(IntentBuilder("IncreaseVolume").require(
        "Volume").require("Increase"))
    def handle_increase_volume(self, message):
        self.__communicate_volume_change(message, 'increase.volume',
                                         *self.__update_volume(+1))

    @intent_handler(IntentBuilder("DecreaseVolume").require(
        "Volume").require("Decrease"))
    def handle_decrease_volume(self, message):
        self.__communicate_volume_change(message, 'decrease.volume',
                                        *self.__update_volume(-1))

    @intent_handler(IntentBuilder("MuteVolume").require(
        "Volume").require("Mute"))
    def handle_mute_volume(self, message):
        speak_message = message.data.get('speak_message', True)
        if speak_message:
            self.speak_dialog('mute.volume')
            wait_while_speaking()
        self._setvolume(0, emit=False)
        self.bus.emit(Message('mycroft.volume.duck'))

    @intent_handler(IntentBuilder("UnmuteVolume").require(
        "Volume").require("Unmute"))
    def handle_unmute_volume(self, message):
        self._setvolume(self.__level_to_volume(self.settings["default_level"]),
                        emit=False)
        self.bus.emit(Message('mycroft.volume.unduck'))

        speak_message = message.data.get('speak_message', True)
        if speak_message:
            self.speak_dialog('reset.volume',
                              data={'volume': self.settings["default_level"]})

    def __volume_to_level(self, volume):
        """
            Convert a 'volume' to a 'level'

            Args:
                volume (int): min_volume..max_volume
            Returns:
                int: the equivalent level
        """
        range = self.MAX_LEVEL - self.MIN_LEVEL
        prop = float(volume - self.settings["min_volume"]) / self.settings["max_volume"]
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

            Returns: tuple(new level code int(0..11),
                           whether level changed (bool))
        """
        old_level = self.__volume_to_level(self.mixer.getvolume()[0])
        new_level = self.__bound_level(old_level + change)
        self.enclosure.eyes_volume(new_level)
        self._setvolume(self.__level_to_volume(new_level))
        return new_level, new_level != old_level

    def __get_volume_level(self, message, default=None):
        level_str = message.data.get('Level', default)
        level = self.settings["default_level"]

        try:
            level = self.VOLUME_WORDS[level_str]
        except KeyError:
            try:
                level = int(level_str)
                if (level > self.MAX_LEVEL):
                    # Guess that the user said something like 100 percent
                    # so convert that into a level value
                    level = self.MAX_LEVEL * level/100
            except ValueError:
                pass

        level = self.__bound_level(level)
        return level


def create_skill():
    return VolumeSkill()
