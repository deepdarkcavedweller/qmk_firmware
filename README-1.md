# QMK Flash

Changes over ZMK keymapping for the wireless version

Changes that have been made over default
1. <https://docs.qmk.fm/tap_hold>
	1. Changed tap-hold delays to 250ms to help with the layer changes with the tap hold buttons.
	1. TODO - Test this and see if 200ms may be better. Right now typing feels good on Layer 0, but may run into some annoyances for layer work.
2. Keymap
	1. differing from the wireless board. Swapped control and gui buttons for better use with windows / linux
	1. No layer 1/2 on the right enter or - buttons
3. Reset button
	3. Added a key bind for the reset button, hopefully this will make the controller go into boot mode.... layer 2 + [ or ]