# Valley animation candidates

55 review clips, 180 drawn pose crops across 10 humans and 6 creatures. Only 8 optimized woodcutter PNG preview frames are currently in this directory; the native-resolution frame package has not been transferred to GitHub yet. The eight original woodcut composite poses contain the stump. The independent wood-chip effect is authored SVG, not a replacement for the missing body/tool separation.

Import the ZIP with the existing `tools/import-chat-assets.py` (the filename starts with fz-), preserving source PNGs and manifest. Verify the archive SHA-256 in animation-review.json before importing. Keep the material in REVIEW; do not auto-promote. The high-resolution human and creature sequences still require consistency checks; the small composite source has visible crop artifacts. Do not claim 8-frame idle or 12-frame chop sequences where only fewer unique poses exist.

At runtime attack/woodcut must fire the contact event once per strike; death clips play once and hold the final frame, and idle and walk loop. Do not derive real impact events from UI draw count.
