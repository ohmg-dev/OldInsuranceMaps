import ImageLayer from 'ol/layer/Image';
import ImageStatic from 'ol/source/ImageStatic';

export function makeImageLayer(source, projection, extent) {
    return new ImageLayer({
        source: new ImageStatic({
            url: source,
            projection: projection,
            imageExtent: extent,
        }),
    })
}