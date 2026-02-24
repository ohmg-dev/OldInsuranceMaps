# Data model & concepts (in progress)

!!! note

    This section still in progress. See [ohmg.dev](https://www.ohmg.dev/concepts) for more information about the structure of the database.

!!! note

    This section mentions `TrimSession`, which is a model that was deprecated a long time ago when multimask was introduced, but should be reintroduced eventually.

All georeferencing activity is stored in `SessionBase` objects, as implemented through the proxy models `PrepSession`, `GeorefSession`, and `TrimSession`. Each proxy model has its own implementation of a `run()` method which uses the information in the `data` field to perform the appropriate actions.

![Data model for the georeference app.](../images/georeference-data-model-sans-links.png)

#### Narrative Explanation

When a user begins preparing a Document, a new `PrepSession` is created. If the user creates cutlines to split the document, this information is saved in the session's `data` field as JSON and then used to run the splitting action that creates new child documents (the original document is not altered).

When a user begins georeferencing a Document, a new `GeorefSession` is created. When the ground control points have been created and submitted through the interface, they are stored as GeoJSON in the session's `data` field and then used to warp the Document and create a Layer. Finally, they are saved separately as `GCP` objects and aggregated into 1 `GCPGroup` per Document. This facilitates iterative editing of the Document's "canonical" GCPs, while also allowing for the reversion to a past set of GCPs if necessary.

Similarly, a user creates a `TrimSession` when they begin trimming a Layer. The mask polygon is stored in the session's `data` and then pushed to the Layer's canonical `LayerMask` object, and applied as a cropped style in Geoserver.
