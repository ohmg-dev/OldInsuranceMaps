import ImageLayer from 'ol/layer/Image';
import TileLayer from 'ol/layer/Tile';
import LayerGroup from 'ol/layer/Group';
import VectorTile from 'ol/layer/VectorTile';
import VectorLayer from 'ol/layer/Vector';

import Point from 'ol/geom/Point';

import Feature from 'ol/Feature';

import GeoJSON from 'ol/format/GeoJSON';
import ImageStatic from 'ol/source/ImageStatic';
import TileJSON from 'ol/source/TileJSON';
import VectorSource from 'ol/source/Vector';
import XYZ from 'ol/source/XYZ';

import { transformExtent } from 'ol/proj';
import Projection from 'ol/proj/Projection';

import { apply } from 'ol-mapbox-style';
import { PMTilesVectorSource } from 'ol-pmtiles';

import Crop from 'ol-ext/filter/Crop';

import { rotateCenterStyle } from "./styles";

// set the extent and projection with 0, 0 at the **top left** of the image
// this is currently the setup for the Georeference interfance, but not for the Splitter!
export function extentFromImageSize(imageSize) {
  return [0, -imageSize[1], imageSize[0], 0];
}

export function projectionFromImageExtent(extent) {
  return new Projection({
    units: 'pixels',
    extent: extent,
  });
}

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


export function makeMBSatelliteStyleLayer(apiKey) {
  return new TileLayer({
    source: new XYZ({
      url: 'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v10/tiles/{z}/{x}/{y}?access_token=' + apiKey,
      tileSize: 512,
      attributions: [
        `© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>`,
      ],
    }),
  });
}

export function makeMBSatelliteRasterLayer(apiKey) {
  return new TileLayer({
    source: new XYZ({
      url: 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.jpg?access_token=' + apiKey,
      tileSize: 512,
      attributions: [
        `© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>`,
      ],
    }),
  })
}

export function makeOFMLayer() {
  const openfreemap = new LayerGroup();
  apply(openfreemap, 'https://tiles.openfreemap.org/styles/liberty');
  return openfreemap;
}

export function makeOFMSatelliteLayer(apiKey) {
  const openfreemap = new LayerGroup({ layers: [
    makeMBSatelliteRasterLayer(apiKey)
  ]});
  apply(openfreemap, "/static/mapstyles/liberty-labels/style.json")
  return openfreemap
}

export function makeBasemaps(mapboxKey) {
  return [
    {
      id: 'osm',
      layer: makeOFMLayer(),
      label: 'Streets',
    },
    {
      id: 'satellite',
      layer: makeMBSatelliteStyleLayer(mapboxKey),
      label: 'Streets+Satellite',
    },
    {
      layer: makeOFMSatelliteLayer(mapboxKey),
      id: 'satellite-new',
      label: 'Streets+Satellite New',
    },
  ];
}

export function makeTitilerXYZUrl(options) {
  // options must be an object with the following properties:
  // {
  //	 host: full address to titiler instance, e.g. https://titiler.oldinsurancemaps.net
  //	 url: url for resource to tile
  //	 doubleEncode: true/false for whether to double encode the returned url (default false)
  //	 colorMapName: name of pre-made colormap to use
  //	 bandNumber: band number to use for colormap
  //	 colorMap: a full custom colormap object to pass through the colormap param
  // }

  // colorMap='{"0": "#e5f5f9","10": "#99d8c9","200": "#2ca25f"}'
  // colorMapParam=`&bidx=1&colormap=${encodeURIComponent(colorMap)}`

  let finalUrl = options.host;
  if (String(options.url).endsWith('.json')) {
    finalUrl += '/mosaicjson/tiles/WebMercatorQuad/{z}/{x}/{y}.png?';
  } else {
    finalUrl += '/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png?';
  }

  const encodedUrl = encodeURIComponent(options.url);
  finalUrl += `&url=${encodedUrl}`;

  if (options.colorMapName) {
    finalUrl += `&colormap_name=${options.colorMapName}`;
  }
  if (options.bandNumber) {
    finalUrl += `&bidx=${options.bandNumber}`;
  }
  if (options.colorMap) {
    const colorMap = encodeURIComponent(options.colorMap);
    finalUrl += `&colormap=${colorMap}`;
  }
  if (options.doubleEncode) {
    finalUrl = encodeURIComponent(finalUrl);
  }

  return finalUrl;
}

export function makeLayerGroupFromLayerSet(options) {
  // options must be an object with the following properties:
  // {
  //	layerSet: serialized item (this includes layers, extent, etc.)
  //	titilerHost: full address to titiler instance, e.g. https://titiler.oldinsurancemaps.net
  //	zIndex: optional zIndex to apply to the returned LayerGroup
  //	excludeLayerId: the id of a single layer that should be omitted from the LayerGroup
  //  applyMultiMask: if a MultiMask is present in the LayerSet, apply it
  // }

  const lyrGroup = new LayerGroup();
  if (!options.layerSet) {
    return lyrGroup;
  }
  options.layerSet.layers.forEach(function (layer) {
    if (layer.slug != options.excludeLayerId && layer.tilejson) {
      // create the actual ol layers and add to group.
      let newLayer = new TileLayer({
        source: new TileJSON({
          tileJSON: layer.tilejson,
          tileSize: 512,
        }),
        extent: transformExtent(layer.tilejson.bounds, 'EPSG:4326', 'EPSG:3857'),
      });

      lyrGroup.getLayers().push(newLayer);

      if (options.applyMultiMask && options.layerSet.multimask_geojson) {
        options.layerSet.multimask_geojson.features.forEach(function (f) {
          if (f.properties.layer == layer.slug) {
            const feature = new GeoJSON().readFeature(f.geometry);
            feature.getGeometry().transform('EPSG:4326', 'EPSG:3857');
            const crop = new Crop({
              feature: feature,
              wrapX: true,
              inner: false,
            });
            newLayer.addFilter(crop);
          }
        });
      }
    }
  });

  options.zIndex && lyrGroup.setZIndex(options.zIndex);
  return lyrGroup;
}

export function makeRotateCenterLayer() {
  const feature = new Feature();
  const pointStyle = rotateCenterStyle;
  const layer = new VectorLayer({
    source: new VectorSource({
      features: [feature],
    }),
    style: pointStyle,
    zIndex: 501,
  });
  return {
    layer: layer,
    feature: feature,
  };
}

export function showRotateCenter(map, layer, feature) {
  if (map && layer && feature) {
    const centerCoords = map.getView().getCenter();
    const point = new Point(centerCoords);
    feature.setGeometry(point);
    layer.setVisible(true);
  }
}

export function removeRotateCenter(layer) {
  if (layer) {
    layer.setVisible(false);
  }
}
