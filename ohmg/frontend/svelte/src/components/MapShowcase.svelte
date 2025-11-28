<script>
  import Link from './common/Link.svelte';

  import MapItem from './cards/MapItem.svelte';

  import LatestAdditions from './lists/LatestAdditions.svelte';

  export let CONTEXT;
  export let FEATURED_MAPS = [];
  export let DOC_CT;
  export let CONT_CT;
  export let SESH_CT;
  export let MAP_CT;
  export let LYR_CT;
</script>

<div>
  <div class="level">
    <div class="level-left">
      <h2>Content overview</h2>
    </div>
    <div class="level-rightn hidden-mobile">
      <em
        >Want to georeference a new map? Make a request through <Link
          href="https://docs.google.com/forms/d/e/1FAIpQLSeF6iQibKEsjIv4fiYIW4vVVxyimLL8sDLX4BLU7HSWsRBOFQ/viewform?usp=sf_link"
          external={true}>this form.</Link
        ></em
      >
    </div>
  </div>
  <div class="hero-banner-inner">
    <div>
      <ul>
        <li>{MAP_CT} maps...</li>
        <li>comprising {DOC_CT} pages/sheets...</li>
        <li>georeferenced by {CONT_CT} users...</li>
        <li>over the course of {SESH_CT} sessions...</li>
        <li>resulting in {LYR_CT} individual layers.</li>
      </ul>
      <h3>Find content</h3>
      <ul>
        <li><Link href="/search/#map">By location</Link></li>
        <li><Link href="/united-states">By state &gt; county &gt; city</Link></li>
        <li><Link href="/search/#items">By map</Link></li>
      </ul>
    </div>
    {#if FEATURED_MAPS}
      <div>
        <h3>Featured maps</h3>
        {#each FEATURED_MAPS as MAP}
          <MapItem {MAP} />
        {/each}
      </div>
    {/if}
    <div>
      <h3>Recently added maps</h3>
      <LatestAdditions {CONTEXT} />
    </div>
  </div>
  <div class="level hidden-non-mobile" style="margin-top:2em;">
    <div class="level-center">
      <em
        >Want to georeference a new map? Make a request through <Link
          href="https://docs.google.com/forms/d/e/1FAIpQLSeF6iQibKEsjIv4fiYIW4vVVxyimLL8sDLX4BLU7HSWsRBOFQ/viewform?usp=sf_link"
          external={true}>this form.</Link
        ></em
      >
    </div>
  </div>
</div>

<style>
  .hero-banner-inner {
    display: flex;
    flex-direction: row;
    justify-content: space-around;
  }

  .hero-banner-inner > div > ul {
    font-size: 1.25em;
    padding: 0;
    list-style: none;
  }
  .hero-banner-inner > div > ul li {
    padding-left: 5px;
  }
  @media only screen and (max-width: 760px) {
    .hero-banner-inner {
      flex-direction: column;
    }
  }
</style>
