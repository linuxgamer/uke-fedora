# Audio Hardware Assets for Xiaomi Pad 7 (uke)

- `fs19xx.fsm`: FourSemi FS19xx smart amplifier calibration and DSP preset firmware required by `snd-soc-fs19xx` driver. Target: `/usr/lib/firmware/qcom/uke/audio/fs19xx.fsm`.
- `asound.state`: Hardware mixer state enabling the 4 smart amplifier switches (TopLeft, TopRight, BottomLeft, BottomRight) and MultiMedia2 TDM audio routing (`SECONDARY_TDM_RX_0 Audio Mixer MultiMedia2 = on`). Target: `/var/lib/alsa/asound.state`.
