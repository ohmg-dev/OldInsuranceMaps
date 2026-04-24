import VectorSource from 'ol/source/Vector';
import ImageStatic from 'ol/source/ImageStatic';
import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import TileWMS from 'ol/source/TileWMS';
import TileJSON from 'ol/source/TileJSON';

import { apply } from 'ol-mapbox-style';

import GeoJSON from 'ol/format/GeoJSON';

import { transformExtent } from 'ol/proj';
import { getCenter } from 'ol/extent';
import Projection from 'ol/proj/Projection';

import Feature from 'ol/Feature';
import Polygon from 'ol/geom/Polygon';
import Point from 'ol/geom/Point';

import Style from 'ol/style/Style';
import Fill from 'ol/style/Fill';
import Stroke from 'ol/style/Stroke';
import RegularShape from 'ol/style/RegularShape';

import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import LayerGroup from 'ol/layer/Group';

import Crop from 'ol-ext/filter/Crop';

export const usaExtent = transformExtent([-125.5, 24.9, -66.9, 49.2], 'EPSG:4326', 'EPSG:3857');

export const onMobile = function() {
  let check = false;
  (function(a){if(/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))) check = true;})(navigator.userAgent||navigator.vendor||window.opera);
  return check;
};

// generate a uuid, code from here:
// https://www.cloudhadoop.com/2018/10/guide-to-unique-identifiers-uuid-guid
export function uuid() {
  var uuidValue = '',
    k,
    randomValue;
  for (k = 0; k < 32; k++) {
    randomValue = (Math.random() * 16) | 0;
    if (k == 8 || k == 12 || k == 16 || k == 20) {
      uuidValue += '-';
    }
    uuidValue += (k == 12 ? 4 : k == 16 ? (randomValue & 3) | 8 : randomValue).toString(16);
  }
  return uuidValue;
}

export function slugify(text) {
  return text
      .toString()                     // Cast to string
      .toLowerCase()                  // Convert to lowercase
      .trim()                         // Remove leading/trailing whitespace
      .normalize('NFD')               // Separate accents from letters
      .replace(/[\u0300-\u036f]/g, '') // Remove accents
      .replace(/\s+/g, '-')           // Replace spaces with hyphens
      .replace(/[^\w-]+/g, '')        // Remove non-word characters (except hyphens)
      .replace(/--+/g, '-');          // Replace multiple hyphens with one
  }

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

export function copyToClipboard(elementId) {
  const copyText = document.getElementById(elementId);
  copyText.select();
  navigator.clipboard.writeText(copyText.value);
  alert('Copied the text: ' + copyText.value);
}

export function makeSatelliteLayer(apiKey) {
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

export function makeOSMLayer() {
  return new TileLayer({
    source: new OSM({
      attributions: [`© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors.`],
    }),
  });
}

export function makeOFMLayer() {
  const openfreemap = new LayerGroup();
  apply(openfreemap, 'https://tiles.openfreemap.org/styles/liberty');
  return openfreemap;
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
      layer: makeSatelliteLayer(mapboxKey),
      label: 'Streets+Satellite',
    },
  ];
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

export function generateFullMaskLayer(map) {
  let projExtent = map.getView().getProjection().getExtent();
  const polygon = new Polygon([
    [
      [projExtent[0], projExtent[1]],
      [projExtent[2], projExtent[1]],
      [projExtent[2], projExtent[3]],
      [projExtent[0], projExtent[3]],
      [projExtent[0], projExtent[1]],
    ],
  ]);
  const layer = new VectorLayer({
    source: new VectorSource({
      features: [new Feature({ geometry: polygon })],
    }),
    style: new Style({
      fill: new Fill({ color: 'rgba(255, 255, 255, 0.5)' }),
    }),
    zIndex: 500,
  });
  layer.setVisible(false);
  return layer;
}

export function makeRotateCenterLayer() {
  const feature = new Feature();
  const pointStyle = new Style({
    image: new RegularShape({
      radius: 10,
      radius2: 1,
      points: 4,
      rotateWithView: true,
      fill: new Fill({ color: '#FF0000' }),
      stroke: new Stroke({
        color: '#FF0000',
        width: 2,
      }),
    }),
  });
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

export function setMapExtent(map, extent4326) {
  if (map) {
    const extent3857 = transformExtent(extent4326, 'EPSG:4326', 'EPSG:3857');
    map.getView().fit(extent3857);
  }
}
