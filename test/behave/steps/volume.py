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


@given("the volume is set to 5")
def given_volume_is_five(context):
    emit_utterance(context.bus, 'Set volume to 5')

    def check_volume_set_to_5(message):
        """Ensure the volume set is set to 5."""
        return message.data['percent'] == 0.5, ""

    message_found, _ = then_wait(
        "mycroft.volume.set", check_volume_set_to_5, context)
    if message_found:
        context.volume = 0.5
        wait_while_speaking()
    context.bus.clear_messages()
    assert message_found


@given("the volume is set to 10")
def given_volume_is_ten(context):
    emit_utterance(context.bus, 'Set volume to 10')

    def check_volume_set_to_10(message):
        """Ensure the volume set is set to 10."""
        return message.data['percent'] == 1.0, ""

    message_found, _ = then_wait(
        "mycroft.volume.set", check_volume_set_to_10, context)
    if message_found:
        context.volume = 1.0
        wait_while_speaking()
    context.bus.clear_messages()
    assert message_found


@then('"mycroft-volume" should decrease the volume')
def then_decrease(context):

    def check_volume_decreased(message):
        """Ensure the volume set is lower than the previous volume."""
        volume_did_decrease = message.data['percent'] < context.volume
        return volume_did_decrease, ""

    message_found, _ = then_wait(
        "mycroft.volume.set", check_volume_decreased, context)
    assert message_found, "No matching message received. "


@then('"mycroft-volume" should increase the volume')
def then_increase(context):

    def check_volume_increased(message):
        """Ensure the volume set is higher than the previous volume."""
        volume_did_decrease = message.data['percent'] > context.volume
        return volume_did_decrease, ""

    message_found, _ = then_wait(
        "mycroft.volume.set", check_volume_increased, context)
    assert message_found, "No matching message received. "
