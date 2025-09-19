<script>
  import SvelteMarkdown from 'svelte-markdown';

  import Link from '../common/Link.svelte';
  import SVGIcon from '../common/SVGIcon.svelte';
  import MapBrowse from '../interfaces/MapBrowse.svelte';

  import LatestAdditions from '../lists/LatestAdditions.svelte';
  import SessionList from '../lists/SessionList.svelte';
  import HowItWorks from './sections/HowItWorks.svelte';
  import LatestBlogPosts from './sections/LatestBlogPosts.svelte';

  export let CONTEXT;
  export let NEWSLETTER_SLUG;
  export let USER_SUBSCRIBED;
  export let PLACES_CT;
  export let MAP_CT;
  export let FEATURED_MAPS = [];

  const blogSection = false;
</script>

<main>
  <section>
    <div>
      <h1 style="word-wrap: break-word;">OldInsuranceMaps.net</h1>
      <p>
        A crowdsourcing site for creating and viewing georeferenced mosaics of historical fire insurance maps from the
        Library of Congress. See <Link href="/#how-it-works">how it works</Link> or visit the <Link
          href="https://about.oldinsurancemaps.net?utm_source=hero">about</Link
        > or <Link href="/faq">FAQ</Link> pages to learn more.
      </p>
    </div>
  </section>
  <section>
    <div class="double-column-section" style="padding:0;">
      <div style="padding:10px;">
        <div style="border-bottom: dashed grey 1px; padding-bottom: 20px;">
          <LatestBlogPosts />
        </div>
        <div class="level is-mobile" style="margin-bottom:0;">
          <div class="level-left">
            <div class="level-item">
              <h3>Newsletter</h3>
            </div>
          </div>
          <div class="level-right">
            <div class="level-item">
              <Link href="/newsletter/{NEWSLETTER_SLUG}/archive/" rightArrow={true}>read past newsletters</Link>
            </div>
          </div>
        </div>
        <form enctype="multipart/form-data" method="post" action="/newsletter/{NEWSLETTER_SLUG}/subscribe/">
          <input type="hidden" name="csrfmiddlewaretoken" value={CONTEXT.csrf_token} />
          <label for="id_email_field" style="margin-right:0; font-size: 1.15em;">Subscribe:</label>
          <input
            type="email"
            name="email_field"
            required=""
            id="id_email_field"
            disabled={USER_SUBSCRIBED}
            placeholder={USER_SUBSCRIBED ? "you're already subscribed!" : ''}
          />
          {#if USER_SUBSCRIBED}
            <Link href="/newsletter/{NEWSLETTER_SLUG}?utm_source=index">manage your subscription</Link>
          {:else}
            <button id="id_submit" title="Subscribe to newsletter" name="submit" value="Subscribe" type="submit"
              >Subscribe</button
            >
          {/if}
        </form>
      </div>
      <div style="padding:0;">
        <div style="padding:10px; min-height:75px;">
          <div class="level" style="margin-bottom:0;">
            <div class="level-left">
              <div class="level-item">
                <h3>{MAP_CT} maps in {PLACES_CT} cities</h3>
              </div>
            </div>
            <div class="level-right">
              <div class="level-item">
                <Link href="/united-states" rightArrow={true}>search all places</Link>
              </div>
            </div>
          </div>
        </div>
        <div class="map-container">
          <MapBrowse {CONTEXT} MAP_HEIGHT={'100%'} />
        </div>
      </div>
    </div>
  </section>
  <section>
    <div>
      <div class="hero-banner-inner">
        {#if FEATURED_MAPS}
          <div>
            <h3>Featured maps</h3>
            <ul>
              {#each FEATURED_MAPS as map}
                <li><Link href={`/map/${map.id}`}>{map.title}</Link></li>
              {/each}
            </ul>
          </div>
        {/if}
        <div>
          <h3>Recently added maps</h3>
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
                external={true}>request more LOC Sanborn maps</Link
              ></em
            ></span
          >
        </div>
      </div>
    </div>
  </section>

  <section id="how-it-works">
    <div>
      <HowItWorks />
    </div>
  </section>

  <section id="latest-activity-section">
    <div>
      <div class="level is-mobile" style="margin-bottom:0;">
        <div class="level-left">
          <div class="level-item">
            <h3>Latest activity</h3>
          </div>
        </div>
        <div class="level-right">
          <div class="level-item">
            <Link href="/activity" rightArrow={true}>all activity</Link>
          </div>
        </div>
      </div>
      <SessionList {CONTEXT} showThumbs={true} />
    </div>
  </section>

  <section style="font-size:1.15em;">
    <div>
      <SvelteMarkdown
        source={`_OldInsuranceMaps.net_ is funded in part by the National Institutes of Health (National Institute on Aging: [R01AG080401](https://reporter.nih.gov/search/bCrnkRo-rkWJJXyXqsj44g/project-details/10582012)) through a partnership with University of Michigan [Institute for Social Research](https://isr.umich.edu/), University of Richmond [Digital Scholarship Lab](https://dsl.richmond.edu/), and the [National Community Reinvestment Coalition](https://ncrc.org). Read more in the [ISR press release](https://isr.umich.edu/news-events/news-releases/grant-to-enable-creation-of-new-data-resources-for-studying-structural-racism/).

We have also worked in partnership with [OpenHistoricalMap](https://openhistoricalmap.org), [HistoryForge](https://historyforge.net), [Midlo Center for New Orleans Studies](https://www.uno.edu/academics/colaehd/la/history/midlo), [The Ohio State University Libraries](https://www.uno.edu/research/centers-and-institutes/midlo), and numerous other individuals who have found this while on their own quest to georeference Sanborn Maps.

A special thanks to individuals who have donated: Kevin H., Andrew M., Peter M., Pete Z., Chris P., Hayden S., and Mike O.

To donate: [paypal.me/oldinsurancemaps](https://paypal.me/oldinsurancemaps)
`}
      />
    </div>
  </section>
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

  section {
    margin-top: 40px;
    padding: 0 20px;
  }

  section > div {
    background: rgba(255, 255, 255, 0.85);
    border: 2px solid black;
    border-radius: 4px;
    padding: 10px;
    margin-bottom: 10px;
  }

  main p {
    font-size: 1.25em;
  }

  #how-it-works {
    scroll-margin-top: 40px;
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

  .double-column-section {
    display: flex;
    gap: 10px;
    padding: 0;
  }

  .double-column-section > div {
    width: 50%;
  }

  .map-container {
    height: calc(100% - 75px);
    border-top: 2px solid black;
    border-left: 2px solid black;
  }

  @media only screen and (max-width: 760px) {
    main {
      max-width: none;
    }

    .hero-banner-inner {
      flex-direction: column;
    }

    .double-column-section {
      flex-direction: column-reverse;
    }

    .double-column-section > div {
      width: 100%;
    }

    .map-container {
      display: none;
    }
  }
</style>
