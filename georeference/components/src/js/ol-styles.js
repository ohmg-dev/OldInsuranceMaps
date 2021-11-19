import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Fill from 'ol/style/Fill';
import RegularShape from 'ol/style/RegularShape';

class Styles {

  empty = new Style();

  trimDraw = new Style({
    stroke: new Stroke({ color: '#fae200', width: 2, })
  });

  gcpHover = new Style({
    image: new RegularShape({
      radius1: 10,
      radius2: 1,
      points: 4,
      rotation: .79,
      fill: new Fill({color: 'red'}),
      stroke: new Stroke({
        color: 'red', width: 2
      })
    })
  });

  gcpDefault = new Style({
    image: new RegularShape({
      radius1: 10,
      radius2: 1,
      points: 4,
      rotation: .79,
      fill: new Fill({color: 'black'}),
      stroke: new Stroke({
        color: 'black', width: 2
      })
    })
  });

  gcpHighlight = new Style({
    image: new RegularShape({
      radius1: 10,
      radius2: 1,
      points: 4,
      rotation: .79,
      fill: new Fill({color: 'rgb(0, 255, 0)'}),
      stroke: new Stroke({
        color: 'rgb(0, 255, 0)', width: 2
      })
    })
  });

  splitPreviewStyle = new Style({
    fill: new Fill({ color: 'rgba(255, 29, 51, 0.1)', }),
    stroke: new Stroke({ color: 'rgba(255, 29, 51, 1)', width: 7.5, }),
  });

  outlineStyle = new Style({
    stroke: new Stroke({ color: '#fae200', width: 2, })
  });

  splitBorderStyle = new Style({
    stroke: new Stroke({ color: '#fae200', width: 2, })
  });

  splitCutLayer = new Style({
    stroke: new Stroke({ color: '#fae200', width: 2, })
  });

} 

export default Styles