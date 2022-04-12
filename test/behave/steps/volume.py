from time import sleep
from behave import given, then

from mycroft.messagebus import Message
from mycroft.audio import wait_while_speaking

from test.integrationtests.voight_kampff import emit_utterance, then_wait


@given("Mycroft audio is muted")
def given_muted(context):
    context.bus.emit(Message('mycroft.volume.mute',
                             data={'speak_message': False}))
    sleep(0.5)


@given("the volume is set to {level}")
def given_volume_is_five(context, level):
    emit_utterance(context.bus, f'Set volume to {level}')
    context.volume = int(level) / 10  # eg 0.5
    sleep(1)
    wait_while_speaking()
    response = context.bus.wait_for_response(
                    Message('mycroft.volume.get'))
    if response and response.data.get('percent'):
        is_volume_set = response.data['percent'] == context.volume
        assert is_volume_set, f"Volume did not get set correctly. Current volume is: {response.data['percent']}"
    context.bus.clear_messages()


@then('"mycroft-volume" should decrease the volume')
def then_decrease(context):
    sleep(0.5)
    response = context.bus.wait_for_response(
                    Message('mycroft.volume.get'))
    if response and response.data.get('percent'):
        volume_decreased = response.data['percent'] < context.volume
        assert volume_decreased, f"Volume did not decrease. Current volume is: {response.data['percent']}"


@then('"mycroft-volume" should increase the volume')
def then_increase(context):
    sleep(0.5)
    response = context.bus.wait_for_response(
                    Message('mycroft.volume.get'))
    if response and response.data.get('percent'):
        volume_increased = response.data['percent'] > context.volume
        assert volume_increased, f"Volume did not increase. Current volume is: {response.data['percent']}"
