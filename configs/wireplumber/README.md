# WirePlumber Audio Rules for Xiaomi Pad 7 (uke)

- `85-uke-speaker-priority.conf`: WirePlumber configuration rule that assigns higher priority (`priority.session = 2000`) to the internal quad-speaker system (`alsa_output.platform-sound-uke.pro-output-1`) over the DisplayPort audio sink (`alsa_output.platform-sound-uke.pro-output-0`). This ensures out-of-the-box speaker output for media players and browsers without hanging unclocked DP pipes. Target: `/usr/share/wireplumber/wireplumber.conf.d/85-uke-speaker-priority.conf`.
