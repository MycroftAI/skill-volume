Feature: mycroft-volume
Scenario Outline: unmute audio
    Given an english speaking user
    And Mycroft audio is muted
     When the user says "<unmute audio>"
     Then "mycroft-volume" should reply with dialog from "reset.volume.dialog"

  Examples: unmute audio
    | unmute audio |
    | unmute |
    | turn sound back on |
    | turn on sound |
    | turn muting off |
    | turn mute off |
    | unmute all sound |
    | unmute the volume |
