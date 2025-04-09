import ImageLayer from 'ol/layer/Image';
import ImageStatic from 'ol/source/ImageStatic';

import VectorTile from 'ol/layer/VectorTile';
import { PMTilesVectorSource } from 'ol-pmtiles';

export function makeImageLayer(source, projection, extent) {
  return new ImageLayer({
    source: new ImageStatic({
      url: source,
      projection: projection,
      imageExtent: extent,
    }),
  });
}

export function makePmTilesLayer(url, attribution, style) {
  return new VectorTile({
    declutter: true,
    source: new PMTilesVectorSource({
      url: url,
      attributions: [attribution],
    }),
    style: style,
    maxResolution: 140,
  });
}
