from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner


class FocusButton(FocusBehavior, Button):
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == "enter":
            self.trigger_action(duration=0.01)
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)


class FocusSpinner(FocusBehavior, Spinner):
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == "enter":
            if self.is_open:
                self.is_open = False
            else:
                self.is_open = True
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)
