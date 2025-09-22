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

  const logoList = [
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/dsl+ur.png',
      link: 'https://dsl.richmond.edu/',
      text: 'Digital Scholarship Lab, University of Richmond',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/ISR-acronym-white.png',
      link: 'https://isr.umich.edu/',
      text: 'Institute for Social Research, University of Michigan',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/ohm-wordmark-3.png',
      link: 'https://openhistoricalmap.org/',
      text: 'OpenHistoricalMap',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/historyforge-text.png',
      link: 'https://historyforge.net/',
      text: 'HistoryForge',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/color_horizontal_transparent.png',
      link: 'https://midlocenter.org/',
      text: 'Midlo Center for New Orleans Studies, University of New Orleans',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/commaplab-uga-weblogo.png',
      link: 'https://www.communitymappinglab.org/',
      text: 'Community Mapping Lab, University of Georgia',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/rowan_logo_stacked_old.png',
      link: 'https://www.rowan.edu/ric-edelman-college/centers/cdhr/',
      text: 'Center for Digital Humanities Research, Rowan University',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/tab-ksu-logo.png',
      link: 'https://www.ksutab.org/',
      text: 'Kansas State University Technical Assistance to Brownfields',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/logo70-final-cuhe.png',
      link: 'https://cuhe.morgan.edu/',
      text: 'Center for Urban Health Equity, Morgan State University',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/osu-lib-horiz-gray-full.png',
      link: 'https://library.osu.edu/',
      text: 'The Ohio State University Libraries',
    },
    {
      src: 'https://raw.githubusercontent.com/ohmg-dev/blog/refs/heads/main/src/assets/logos/uiuc+herop.png',
      link: 'https://healthyregions.org/',
      text: 'Healthy Regions & Policies Lab, University of Illinois Urbana-Champaign',
    },
  ];
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

  <section>
    <div class="double-column-section">
      <div class="supporter-text">
        <div class="level is-mobile" style="margin-bottom:0;">
          <div class="level-left">
            <div class="level-item">
              <h3>Support</h3>
            </div>
          </div>
        </div>
        <SvelteMarkdown
          source={`_OldInsuranceMaps.net_ is funded in part by the National Institutes of Health (National Institute on Aging: [R01AG080401](https://reporter.nih.gov/search/bCrnkRo-rkWJJXyXqsj44g/project-details/10582012)) through a partnership with University of Michigan [Institute for Social Research](https://isr.umich.edu/), University of Richmond [Digital Scholarship Lab](https://dsl.richmond.edu/), and the [National Community Reinvestment Coalition](https://ncrc.org). Read more in the [ISR press release](https://isr.umich.edu/news-events/news-releases/grant-to-enable-creation-of-new-data-resources-for-studying-structural-racism/).

We have also worked in partnership with [OpenHistoricalMap](https://openhistoricalmap.org), [HistoryForge](https://historyforge.net), [Midlo Center for New Orleans Studies](https://www.uno.edu/academics/colaehd/la/history/midlo), and have supported community georeferencing events at [The Ohio State University Libraries](https://library.osu.edu/), Rowan University's [Center for Digital Humanities Research](https://www.rowan.edu/ric-edelman-college/centers/cdhr/), the [Community Mapping Lab](https://www.communitymappinglab.org/) at University of Georgia, and the [Center for Urban Health Equality at Morgan State University](https://cuhe.morgan.edu/).

OIM proudly supports graduate researchers and independent mappers, especially those who find this site while on a quest to georeference Sanborn maps of their home! Making these maps more accessible is what the project is all about.

And a very special thanks goes out to those individuals who have donated to the project: Kevin H., Andrew M., Peter M., Pete Z., Chris P., Hayden S., and Mike O. Thank you!

To donate: [paypal.me/oldinsurancemaps](https://paypal.me/oldinsurancemaps)
  `}
        />
      </div>
      <div class="logo-list-container">
        {#each logoList as logo}
          <a href={logo.link} target="_blank"><img src={logo.src} class="logo-image" alt={logo.text} /></a>
        {/each}
      </div>
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

  .supporter-text {
    width: 40%;
    padding: 10px;
  }

  .map-container {
    height: calc(100% - 75px);
    border-top: 2px solid black;
    border-left: 2px solid black;
  }

  .logo-list-container {
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    width: 60%;
    padding: 20px;
    gap: 20px;
  }

  .logo-image {
    max-height: 45px;
    max-width: 250px;
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
