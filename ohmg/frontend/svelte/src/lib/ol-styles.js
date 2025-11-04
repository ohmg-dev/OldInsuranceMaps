import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Circle from 'ol/style/Circle';
import Fill from 'ol/style/Fill';
import RegularShape from 'ol/style/RegularShape';

export const colors = {
  black: '#000000',
  red: '#ff0000',
  mainBlue: '#2c689c',
  brightBlue: '#419eb6',
  white: '#FFFFFF',
  aquaGreen: '#45c19c',
  highlighter: 'rgba(250, 226, 0, .9)',
  transparentRed: 'rgba(255, 29, 51, 0.1)',
};

export function makeCircle(fillColor, outlineColor) {
  outlineColor = outlineColor ? outlineColor : colors.black;
  return new Circle({
    radius: 5,
    fill: new Fill({
      color: fillColor,
    }),
    stroke: new Stroke({ color: outlineColor, width: 2 }),
  });
}

// MULTIMASK INTERFACE

// note: multimask styles are created within the mm component, as they depend on
// data generated from the layer content. colors are stored here though.

export const mmColors = {
  unsnapped: colors.white,
  snapped: colors.aquaGreen,
  hover: colors.red,
  draw: colors.brightBlue,
};

// MAP BROWSE INTERFACE

export const browseMapStyle = new Style({
  image: new Circle({
    fill: new Fill({ color: colors.mainBlue }),
    stroke: new Stroke({ color: colors.black, width: 2 }),
    radius: 6,
  }),
});

// GEOREFERENCE INTERFACE

export const gcpColors = {
  default: colors.black,
  hover: colors.red,
  selected: colors.brightBlue,
};

// this is the white outline cross that sits behind every gcp style
const gcpOutline = new Style({
  image: new RegularShape({
    radius: 10,
    radius2: 0,
    points: 4,
    rotation: 0.79,
    fill: new Fill({ color: colors.white }),
    stroke: new Stroke({
      color: colors.white,
      width: 5,
    }),
  }),
});

// create the gcp styles, essentially different fill colors to sit
// on top of the outline.
export function makeGcpX(color) {
  return new Style({
    image: new RegularShape({
      radius: 10,
      radius2: 0,
      points: 4,
      rotation: 0.79,
      stroke: new Stroke({
        color: color,
        width: 2,
      }),
    }),
  });
}

const smallCross = new Style({
  image: new RegularShape({
    radius: 5,
    radius2: 0,
    points: 4,
    rotation: 0,
    stroke: new Stroke({
      color: 'black',
      width: 2,
    }),
  }),
});

export const gcpStyles = {
  default: [gcpOutline, makeGcpX(gcpColors.default)],
  hover: [gcpOutline, makeGcpX(gcpColors.hover)],
  selected: [gcpOutline, makeGcpX(gcpColors.selected)],
  snapTarget: smallCross,
};

export const parcelStyles = {
  active: new Style({
    stroke: new Stroke({
      color: 'red',
      width: 1,
    }),
  }),
  inactive: new Style({
    stroke: new Stroke({
      color: 'grey',
      width: 1,
    }),
  }),
};

export const emptyStyle = new Style();

// SPLIT INTERFACE

export const splitStyles = {
  preview: new Style({
    fill: new Fill({ color: colors.transparentRed }),
    stroke: new Stroke({ color: colors.highlighter, width: 7.5 }),
  }),

  border: new Style({
    stroke: new Stroke({ color: colors.brightBlue, width: 2 }),
  }),

  draw: new Style({
    stroke: new Stroke({ color: colors.brightBlue, width: 2 }),
    image: makeCircle(colors.brightBlue, colors.white),
  }),

  modify: new Style({
    image: makeCircle(colors.brightBlue, colors.white),
  }),
};
