<script>
  import Link from '../../common/Link.svelte';
  import SVGIcon from '../../common/SVGIcon.svelte';
</script>

<h2>How it Works</h2>
<div id="step-list">
  <div>
    <div>
      <SVGIcon icon="volume" size="lg" />
    </div>
    <p>
      Digital scans of Sanborn maps are available through the <Link
        href="https://loc.gov/collections/sanborn-maps"
        external={true}>Library of Congress</Link
      > and are pulled into this site through their <Link
        href="https://www.loc.gov/apis/json-and-yaml/requests/"
        external={true}>JSON API</Link
      >, generating a "Map Summary" page (<Link href="/map/sanborn03275_001?utm_source=index">Baton Rouge, 1885</Link>).
    </p>
  </div>
  <div>
    <div>
      <SVGIcon icon="document" size="lg" />
    </div>
    <p>
      Users <Link href="/split/244/">prepare each sheet</Link> in the volume, sometimes splitting it into multiple regions,
      each to be georeferenced individually (<Link href="/document/244?utm_source=index">Baton Rouge, 1885, page 1</Link
      >).
    </p>
  </div>
  <div>
    <div>
      <SVGIcon icon="layer" size="lg" />
    </div>
    <p>
      Next, each document must be georeferenced by <Link href="/georeference/3097?utm_source=index"
        >creating ground control points</Link
      >, linking features on the old map with latitude/longitude coordinates to create a geospatial layer (<Link
        href="/layer/389?utm_source=index">Baton Rouge, 1885, page 1, part 3</Link
      >).
    </p>
  </div>
  <div>
    <div>
      <SVGIcon icon="webmap" size="lg" />
    </div>
    <p>
      As they are georeferenced, layers slowly build a collage of all the content from a given volume, and their
      overlapping margins <Link href="/map/sanborn03275_001?utm_source=index#multimask">must be trimmed</Link> to create
      a seamless mosaic.
    </p>
  </div>
  <div>
    <div>
      <SVGIcon icon="pinmap" size="lg" />
    </div>
    <p>
      Finally, all volume mosaics for a given locale are automatically aggregated into a simple web viewer so you can
      easily compare different years and current maps (<Link href="/viewer/baton-rouge-la?utm_source=index"
        >Baton Rouge viewer</Link
      >).
    </p>
  </div>
  <h4>
    Want to learn more? Visit the <Link href="https://about.oldinsurancemaps.net?utm_source=index" external={true}
      >documentation site</Link
    >.
  </h4>
</div>

<style>
  #step-list > div {
    display: flex;
    align-items: center;
    padding-bottom: 5px;
    margin-bottom: 5px;
    border-bottom: dashed grey 1px;
  }

  #step-list > div:first-child {
    padding-top: 5px;
    border-top: dashed grey 1px;
  }

  #step-list div > div {
    min-width: 85px;
  }

  #step-list div > p {
    font-size: 1.25em;
    margin-bottom: 0px;
  }
</style>
