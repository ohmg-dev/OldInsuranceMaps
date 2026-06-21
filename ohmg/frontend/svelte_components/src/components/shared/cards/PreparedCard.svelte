<script>
  import ArrowCounterClockwise from 'phosphor-svelte/lib/ArrowCounterClockwise';
  import Broom from 'phosphor-svelte/lib/Broom';
  import FileText from 'phosphor-svelte/lib/FileText';
  import MapPin from 'phosphor-svelte/lib/MapPin';

  import { openModal } from '../../base/Modal.svelte';
  import Link from '../../base/Link.svelte';
  import BaseCard from '../../base/Card.svelte';

  export let CONTEXT;
  export let region;
  export let sessionLocks;
  export let userCanEdit;
  export let modalLyrUrl;
  export let modalExtent;
  export let modalIsGeospatial;
  export let reinitModalMap;
  export let documentToUnprepare;
  export let regionToSetAsNonMap;
  export let regionToSkip;
</script>

<BaseCard>
  <div slot="card-top">
    <Link href={region.urls.resource} title={region.title}>{region.nickname}</Link>
  </div>
  <div slot="card-middle">
    <button
      title="Open image preview"
      class="thumbnail-btn"
      on:click={() => {
        modalLyrUrl = region.urls.image;
        modalExtent = [0, -region.image_size[1], region.image_size[0], 0];
        modalIsGeospatial = false;
        openModal('modal-simple-viewer');
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
          <Link href={region.urls.georeference} title="Begin georeferencing">
            <MapPin /> georeference
          </Link>
        </li>
        <li>
          <button
            disabled={!CONTEXT.user.is_staff && CONTEXT.user.username != region.created_by}
            class="is-text-link"
            title={!CONTEXT.user.is_staff && CONTEXT.user.username != region.created_by
              ? `Only ${region.created_by} or an admin and can undo this preparation`
              : 'Undo preparation'}
            style="display:flex; align-items:center;"
            on:click={() => {
              documentToUnprepare = region.document_id;
              openModal('modal-confirm-unprepare')
            }}
          >
            <ArrowCounterClockwise /> unprepare</button
          >
        </li>
        <li>
          <button
            class="is-text-link"
            title="Move to Non-map section"
            on:click={() => {
              regionToSetAsNonMap = region.id;
              openModal('modal-confirm-set-nonmap')
            }}
          >
            <FileText /> set as non-map</button
          >
        </li>
        <li>
          <button
            class="is-text-link"
            title="Skip this piece (for now)"
            on:click={() => {
              regionToSkip = region.id;
              openModal("modal-confirm-skip-region")
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
