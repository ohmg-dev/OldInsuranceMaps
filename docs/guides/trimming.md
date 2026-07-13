# Creating a MultiMask

Overlapping edges of layers cause messy mosaics, so a mask must be added to each layer to remove its margins. These masks should all be contiguous (sharing adjacent borders and vertices) so it is best to handle them at the map-level, not by masking each layer individually. This is the idea behind a **MultiMask**, which is a unified collection of masks for all layers within a map.

![The multitrim interface.](../images/multitrim.gif)

## Masking across multiple volumes

In large cities it is common to have multiple volumes for a single atlas edition, each volume only covering a subset of the entire city. In the OIM data model, these volumes are treated as separate entities, so while the pages within each one can be carefully masked to form a mosaic, there is no affordance for combining those mosaics across all volumes within an edition. This is something we hope to support in the future.