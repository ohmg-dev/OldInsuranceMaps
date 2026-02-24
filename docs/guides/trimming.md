# Creating a MultiMask

Overlapping edges of layers cause messy mosaics, so a mask must be added to each layer to remove its margins. These masks should all be contiguous (sharing adjacent borders and vertices) so it is best to handle them at the map-level, not by masking each layer individually. This is the idea behind a **MultiMask**, which is a unified collection of masks for all layers within a map.

![The multitrim interface.](../images/multitrim.gif)