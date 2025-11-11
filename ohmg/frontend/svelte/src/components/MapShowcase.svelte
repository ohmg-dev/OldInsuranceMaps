<script>
  import Link from './common/Link.svelte';

  import LatestAdditions from './lists/LatestAdditions.svelte';

  export let CONTEXT;
  export let FEATURED_MAPS = [];
  export let PLACES_CT;
  export let MAP_CT;
</script>

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

<style>
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
</style>
