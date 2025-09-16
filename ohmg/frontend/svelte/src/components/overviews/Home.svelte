<script>
  import SvelteMarkdown from 'svelte-markdown';

  import Link from '../common/Link.svelte';
  import SVGIcon from '../common/SVGIcon.svelte';
  import MapBrowse from '../interfaces/MapBrowse.svelte';

  import LatestAdditions from '../lists/LatestAdditions.svelte';
  import SessionList from '../lists/SessionList.svelte';

  export let CONTEXT;
  export let NEWSLETTER_SLUG;
  export let USER_SUBSCRIBED;
  export let PLACES_CT;
  export let MAP_CT;
  export let FEATURED_MAPS = [];

  let showBrowseMap = !CONTEXT.on_mobile;
  $: showBrowseMapBtnLabel = showBrowseMap ? 'Hide map finder' : 'Show map finder';

  const urlSegs = window.location.href.split('/');
</script>

<main>
  <div class="homepage-section">
    <div>
      <h1 style="word-wrap: break-word;">OldInsuranceMaps.net</h1>
      <p>
        A crowdsourcing site for creating and viewing georeferenced mosaics of historical fire insurance maps from the
        Library of Congress. See <Link href="/#how-it-works">how it works</Link> or visit the <Link
          href="https://about.oldinsurancemaps.net?utm_source=hero"
          external={true}>about</Link
        > or <Link href="https://about.oldinsurancemaps.net/faq?utm_source=hero">FAQ</Link> pages to learn more.
      </p>
    </div>
  </div>
  <div class="homepage-section">
    <div style="padding:0;">
      <div style="padding:5px;">
        <h3>Explore georeferenced maps from {PLACES_CT} locations...</h3>
        <p>Click a point to access maps of that locale, or <Link href="/united-states">search by place name</Link>.</p>
      </div>
      {#if CONTEXT.on_mobile}<span
          ><button
            title="Show browsable map interface"
            class="link-btn"
            on:click={() => {
              showBrowseMap = !showBrowseMap;
            }}>{showBrowseMapBtnLabel}</button
          ></span
        >{/if}
      {#if showBrowseMap}
        <MapBrowse {CONTEXT} MAP_HEIGHT={'400'} EMBEDDED={true} />
      {/if}
    </div>
  </div>

  <div class="homepage-section">
    <div>
      <div class="hero-banner-inner">
        {#if FEATURED_MAPS}
          <div>
            <h3>Featured</h3>
            <ul>
              {#each FEATURED_MAPS as map}
                <li><Link href={`/map/${map.id}`}>{map.title}</Link></li>
              {/each}
            </ul>
          </div>
        {/if}
        <div>
          <h3>Recently added</h3>
          <LatestAdditions {CONTEXT} />
          <span
            ><em
              >Want to see more? View <Link href="/search/#items">all items</Link> and sort by
              <strong>Load date</strong>.</em
            ></span
          >
        </div>
        <div>
          <h3>Browse all</h3>
          <ul>
            <li><Link href="/search/#map">By location ({PLACES_CT})</Link></li>
            <li><Link href="/search/#places">By place name ({PLACES_CT})</Link></li>
            <li><Link href="/search/#places">By item ({MAP_CT})</Link></li>
          </ul>
          <span
            ><em
              ><Link
                href="https://docs.google.com/forms/d/e/1FAIpQLSeF6iQibKEsjIv4fiYIW4vVVxyimLL8sDLX4BLU7HSWsRBOFQ/viewform?usp=sf_link"
                external={true}>request more LOC maps</Link
              ></em
            ></span
          >
        </div>
      </div>
    </div>
  </div>
  {#if NEWSLETTER_SLUG}
    <div class="homepage-section">
      <div>
        <div class="level" style="margin-bottom:0;">
          <div class="level-left">
            <div class="level-item">
              <h3>Newsletter</h3>
            </div>
          </div>
          <div class="level-right">
            <div class="level-item">
              <Link href="/newsletter/{NEWSLETTER_SLUG}/archive/">view the archive &rarr;</Link>
            </div>
          </div>
        </div>
        <form enctype="multipart/form-data" method="post" action="/newsletter/{NEWSLETTER_SLUG}/subscribe/">
          <input type="hidden" name="csrfmiddlewaretoken" value={CONTEXT.csrf_token} />
          <label for="id_email_field" style="margin-right:0; font-size: 1.15em;">Subscribe:</label>
          <input type="email" name="email_field" required="" id="id_email_field" disabled={USER_SUBSCRIBED} />
          {#if USER_SUBSCRIBED}
            <Link href="/newsletter/{NEWSLETTER_SLUG}?utm_source=index">manage subscription</Link>
          {:else}
            <button id="id_submit" title="Submit newsletter subscription" name="submit" value="Subscribe" type="submit"
              >Subscribe</button
            >
          {/if}
        </form>
      </div>
    </div>
  {/if}

  <div id="how-it-works" class="homepage-section">
    <div>
      <h3>How it Works</h3>
      <div id="step-list">
        <div>
          <div>
            <SVGIcon icon="volume" size="lg" />
          </div>
          <p>
            Digital scans of Sanborn maps are available through the <Link
              href="https://loc.gov/collections/sanborn-maps"
              external={true}>Library of Congress</Link
            > and are pulled into this site through the LOC <Link
              href="https://www.loc.gov/apis/json-and-yaml/requests/"
              external={true}>JSON API</Link
            >, generating a "Map Summary" page (<Link href="/map/sanborn03275_001/?utm_source=index"
              >Baton Rouge, 1885</Link
            >).
          </p>
        </div>
        <div>
          <div>
            <SVGIcon icon="document" size="lg" />
          </div>
          <p>
            Users <Link href="/split/244/">prepare each sheet</Link> in the volume, sometimes splitting it into multiple
            documents, each to be georeferenced individually (<Link href="/document/244?utm_source=index"
              >Baton Rouge, 1885, page 1</Link
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
            Finally, all volume mosaics for a given locale are automatically aggregated into a simple web viewer so you
            can easily compare different years and current maps (<Link href="/viewer/baton-rouge-la?utm_source=index"
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
    </div>
  </div>

  <div class="homepage-section" style="min-height:750px;">
    <div>
      <div class="level" style="margin-bottom:0;">
        <div class="level-left">
          <div class="level-item">
            <h3>Latest activity</h3>
          </div>
        </div>
        <div class="level-right">
          <div class="level-item">
            <Link href="/activity">all activity &rarr;</Link>
          </div>
        </div>
      </div>
      <SessionList {CONTEXT} showThumbs={true} />
    </div>
  </div>

  <div class="homepage-section" style="font-size:1.15em;">
    <div>
      <SvelteMarkdown
        source={`_OldInsuranceMaps.net_ is funded in part by the National Institutes of Health (National Institute on Aging: [R01AG080401](https://reporter.nih.gov/search/bCrnkRo-rkWJJXyXqsj44g/project-details/10582012)) through a partnership with University of Michigan [Institute for Social Research](https://isr.umich.edu/), University of Richmond [Digital Scholarship Lab](https://dsl.richmond.edu/), and the [National Community Reinvestment Coalition](https://ncrc.org). Read more in the [ISR press release](https://isr.umich.edu/news-events/news-releases/grant-to-enable-creation-of-new-data-resources-for-studying-structural-racism/).

We have also worked in partnership with [OpenHistoricalMap](https://openhistoricalmap.org), [HistoryForge](https://historyforge.net), [Midlo Center for New Orleans Studies](https://www.uno.edu/academics/colaehd/la/history/midlo), [The Ohio State University Libraries](https://www.uno.edu/research/centers-and-institutes/midlo), and numerous other individuals who have found this while on their own quest to georeference Sanborn Maps.

A special thanks to individuals who have donated: Kevin H., Andrew M., Peter M., Pete Z., Chris P., Hayden S., and Mike O.

To donate: [paypal.me/oldinsurancemaps](https://paypal.me/oldinsurancemaps)
`}
      />
    </div>
  </div>
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    margin-right: -15px;
    margin-left: -15px;
    background:
      linear-gradient(0deg, rgba(255 255 255 / 60%), rgba(255 255 255 / 60%)),
      url(/static/img/old-basin-canal-tall-50qual-crop.jpg);
    background-size: 100%;
  }

  main > div {
    margin-top: 40px;
    padding: 0 20px;
  }

  main p {
    font-size: 1.25em;
  }

  #how-it-works {
    scroll-margin-top: 40px;
  }

  .homepage-section > div {
    background: rgba(255, 255, 255, 0.85);
    border: 2px solid black;
    border-radius: 4px;
    padding: 10px;
    margin-bottom: 10px;
  }

  .hero-banner-inner {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
  }

  .hero-banner-inner > div > ul {
    font-size: 1.25em;
    padding: 0;
    list-style: none;
  }
  .hero-banner-inner > div > ul li {
    padding-left: 5px;
  }

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
    font-size: 1.1em;
    margin-bottom: 0px;
  }

  button.link-btn {
    color: #2c689c;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.25em;
  }

  @media only screen and (max-width: 760px) {
    main {
      max-width: none;
    }

    .hero-banner-inner {
      flex-direction: column;
    }
  }
</style>
