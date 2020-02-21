from behave import given

from mycroft.messagebus import Message
from time import sleep

@given("Mycroft audio is muted")
def given_muted(context):
    context.bus.emit(Message('mycroft.volume.mute',
                             data={'speak_message': False}))
    sleep(0.5)
