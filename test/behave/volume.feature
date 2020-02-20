Feature: volume control

  Scenario Outline: turning up the volume
    Given an english speaking user
     When the user says "<volume up>"
     Then "mycroft-volume" should reply with dialog from "increase.volume.dialog"

  Examples:
    | increase volume |
    | volume up |
    | turn it up |
    | louder |
    | more sound |
    | more audio |
    | higher volume |
    | raise the volume |
    | boost volume |
    | turn up the volume |
    | crank it up |
    | crank volume |
    | make it louder |

  Scenario Outline: turning down the volume
    Given an english speaking user
     When the user says "<volume down>"
     Then "mycroft-volume" should reply with dialog from "decrease.volume.dialog"

  Examples:
    | decrease volume |
    | volume down |
    | turn it down |
    | quiter please |
    | less sound |
    | lower volume |
    | reduce volume |
    | quieter |
    | less volume |
    | lower sound |
    | make it quieter |
    | make it lower |
    | make it softer |

  Scenario Outline: change volume to x
    Given an enlish speaking user
     When the user says "<change volume to x>"
     Then "mycroft-volume" should reply with dialog from "set.volume.dialog"

  Examples:
    | change volume to 8 |
    | set volume to 9 |
    | set audio to 6 |
    | increase volume  to 10 |
    | decrease volume to 4 |
    | raise volume to 8 |
    | lower volume to 4 |
    | volume 8 |
    | volume 80 percent |

  Scenario Outline: change volume to x
    Given an enlish speaking user
     When the user says "<change volume to x>"
     Then "mycroft-volume" should reply with dialog from "max.volume.dialog"

  Examples:
    | max volume |
    | maximum volume |
    | loudest volume |
    | max audio |
    | maximum audio |
    | max sound |
    | maximum sound |
    | turn it up all the way |
    | set volume to maximum |
    | highest volume |
    | raise volume to max |
    | raise volume all the way |
