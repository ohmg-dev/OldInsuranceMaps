<script>
  import '../css/shared.css';
  import Browse from './overviews/Browse.svelte';
  import Home from './overviews/Home.svelte';
  import Place from './overviews/Place.svelte';
  import Participants from './lists/Participants.svelte';

  export let PAGE_NAME = '';
  export let PARAMS = {};
  export let CONTEXT = {};
</script>

{#if PAGE_NAME == 'home'}
  <Home
    {CONTEXT}
    NEWSLETTER_SLUG={PARAMS.NEWSLETTER_SLUG}
    USER_SUBSCRIBED={PARAMS.USER_SUBSCRIBED}
    PLACES_CT={PARAMS.PLACES_CT}
    MAP_CT={PARAMS.MAP_CT}
    FEATURED_MAPS={PARAMS.FEATURED_MAPS}
    MAP_FILTER_LIST={PARAMS.MAP_FILTER_LIST}
  />
{:else if PAGE_NAME == 'profiles'}
  <Participants {CONTEXT} />
{:else if PAGE_NAME == 'place'}
  <Place {CONTEXT} PLACE={PARAMS.PLACE} />
{:else if PAGE_NAME == 'browse'}
  <Browse {CONTEXT} PLACES_CT={PARAMS.PLACES_CT} MAP_CT={PARAMS.MAP_CT} />
{/if}
