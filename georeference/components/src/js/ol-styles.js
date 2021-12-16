import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Circle from 'ol/style/Circle';
import Fill from 'ol/style/Fill';
import RegularShape from 'ol/style/RegularShape';

const btnBlue = '#2c689c';

const interactionPointer = new Circle({
  fill: new Fill({ color: btnBlue, }),
  stroke: new Stroke({ color: '#ffffff', width: 1, }),
  radius: 5,
})

class Styles {

  empty = new Style();

  gcpHover = new Style({
    image: new RegularShape({
      radius1: 10,
      radius2: 1,
      points: 4,
      rotation: .79,
      fill: new Fill({color: "#27ebe7"}),
      stroke: new Stroke({
        color: "#27ebe7", width: 2
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
      fill: new Fill({color: "#bb2c80" }),
      stroke: new Stroke({
        color: "#bb2c80", width: 2
      })
    })
  });

  splitPreviewStyle = new Style({
    fill: new Fill({ color: 'rgba(255, 29, 51, 0.1)', }),
    stroke: new Stroke({ color: 'rgba(250, 226, 0, .9)', width: 7.5, }),
  });

  splitBorderStyle = new Style({
    stroke: new Stroke({ color: btnBlue, width: 2, })
  });

  polyDraw = new Style({  
    stroke: new Stroke({ color: btnBlue, width: 2, }),
    image: interactionPointer,
  });

  polyModify = new Style({
    image: interactionPointer,
  });

} 

export default Styles