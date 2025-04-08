<script>
  import ArrowCounterClockwise from 'phosphor-svelte/lib/ArrowCounterClockwise';
  import Broom from 'phosphor-svelte/lib/Broom';
  import FileText from 'phosphor-svelte/lib/FileText';
  import MapPin from 'phosphor-svelte/lib/MapPin';

  import { getModal } from '../modals/BaseModal.svelte';

  import Link from '../common/Link.svelte';

  import BaseCard from './BaseCard.svelte';

  export let CONTEXT;
  export let region;
  export let sessionLocks;
  export let userCanEdit;
  export let modalLyrUrl;
  export let modalExtent;
  export let modalIsGeospatial;
  export let reinitModalMap;
  export let postDocumentUnprepare;
  export let postRegionCategory;
  export let postSkipRegion;
</script>

<BaseCard>
  <div slot="card-top">
    <Link href={region.urls.resource} title={region.title}>{region.nickname}</Link>
  </div>
  <div slot="card-middle">
    <button
      class="thumbnail-btn"
      on:click={() => {
        modalLyrUrl = region.urls.image;
        modalExtent = [0, -region.image_size[1], region.image_size[0], 0];
        modalIsGeospatial = false;
        getModal('modal-simple-viewer').open();
        reinitModalMap = [{}];
      }}
    >
      <img style="cursor:zoom-in" src={region.urls.thumbnail} alt={region.title} />
    </button>
  </div>
  <div slot="card-bottom">
    {#if sessionLocks.regs[region.id]}
      <ul style="text-align:center">
        <li><em>georeferencing in progress...</em></li>
        <li>user: {sessionLocks.regs[region.id].user.username}</li>
      </ul>
    {:else if userCanEdit}
      <ul>
        <li>
          <Link href={region.urls.georeference} title="georeference this document">
            <MapPin /> georeference
          </Link>
        </li>
        <li>
          <button
            disabled={!CONTEXT.user.is_staff && CONTEXT.user.username != region.created_by}
            class="is-text-link"
            title={!CONTEXT.user.is_staff && CONTEXT.user.username != region.created_by ? `Only ${region.created_by} or an admin and can undo this preparation.` : 'Undo all preparation.'}
            style="display:flex; align-items:center;"
            on:click={() => {
              postDocumentUnprepare(region.document_id);
            }}
          >
            <ArrowCounterClockwise /> unprepare</button
          >
        </li>
        <li>
          <button
            class="is-text-link"
            title="click to move this document to the non-map section"
            on:click={() => {
              postRegionCategory(region.id, 'non-map');
            }}
          >
            <FileText /> set as non-map</button
          >
        </li>
        <li>
          <button
            class="is-text-link"
            title="click to move this document to the non-map section"
            on:click={() => {
              postSkipRegion(region.id, true);
            }}
          >
            <Broom /> skip this piece</button
          >
        </li>
        <li><em>{region.created_by}</em></li>
      </ul>
    {/if}
  </div>
</BaseCard>

<style>
  img {
    margin: 15px;
    max-height: 200px;
    max-width: 200px;
    object-fit: scale-down;
  }
</style>
