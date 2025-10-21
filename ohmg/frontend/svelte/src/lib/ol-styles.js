import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Circle from 'ol/style/Circle';
import Fill from 'ol/style/Fill';
import RegularShape from 'ol/style/RegularShape';
import MultiPoint from 'ol/geom/MultiPoint';

const btnBlue = '#2c689c';

const interactionPointer = new Circle({
  fill: new Fill({ color: btnBlue }),
  stroke: new Stroke({ color: '#ffffff', width: 1 }),
  radius: 5,
});

const browseMapCircle = new Style({
  image: new Circle({
    fill: new Fill({ color: '#2c689c' }),
    stroke: new Stroke({ color: '#000000', width: 2 }),
    radius: 6,
  }),
});

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

// this is the white outline cross that sits behind every gcp style
const gcpOutline = new Style({
  image: new RegularShape({
    radius: 10,
    radius2: 0,
    points: 4,
    rotation: 0.79,
    fill: new Fill({ color: '#ffffff' }),
    stroke: new Stroke({
      color: '#ffffff',
      width: 5,
    }),
  }),
});

// create the gcp styles, essentially different fill colors to sit
// on top of the outline.
const gcpDefault = new Style({
  image: new RegularShape({
    radius: 10,
    radius2: 0,
    points: 4,
    rotation: 0.79,
    stroke: new Stroke({
      color: 'black',
      width: 2,
    }),
  }),
});
const gcpHover = new Style({
  image: new RegularShape({
    radius: 10,
    radius2: 0,
    points: 4,
    rotation: 0.79,
    stroke: new Stroke({
      color: 'red',
      width: 2,
    }),
  }),
});
const gcpHighlight = new Style({
  image: new RegularShape({
    radius: 10,
    radius2: 0,
    points: 4,
    rotation: 0.79,
    // fill: new Fill({color: '#00ff00'}),
    stroke: new Stroke({
      color: '#419EB6',
      width: 2,
    }),
  }),
});

class Styles {
  empty = new Style();

  browseMapStyle = browseMapCircle;
  gcpDefault = [gcpOutline, gcpDefault];
  gcpHover = [gcpOutline, gcpHover];
  gcpHighlight = [gcpOutline, gcpHighlight];

  splitPreviewStyle = new Style({
    fill: new Fill({ color: 'rgba(255, 29, 51, 0.1)' }),
    stroke: new Stroke({ color: 'rgba(250, 226, 0, .9)', width: 7.5 }),
  });

  splitBorderStyle = new Style({
    stroke: new Stroke({ color: btnBlue, width: 2 }),
  });

  polyDraw = new Style({
    stroke: new Stroke({ color: btnBlue, width: 2 }),
    image: interactionPointer,
  });

  polyModify = new Style({
    image: interactionPointer,
  });

  redOutline = new Style({
    stroke: new Stroke({
      color: 'red',
      width: 1,
    }),
  });
  greyOutline = new Style({
    stroke: new Stroke({
      color: 'grey',
      width: 1,
    }),
  });
  smallCross = smallCross;
}

export default Styles;
