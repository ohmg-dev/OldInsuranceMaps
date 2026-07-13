<script>
  import Broom from 'phosphor-svelte/lib/Broom';

  import { openModal } from '../../base/Modal.svelte';
  import Link from '../../base/Link.svelte';
  import BaseCard from '../../base/Card.svelte';

  export let region;
  export let sessionLocks;
  export let userCanEdit;
  export let modalLyrUrl;
  export let modalExtent;
  export let modalIsGeospatial;
  export let reinitModalMap;
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
          <button
            class="is-text-link"
            title="Move to the Prepared section"
            on:click={() => {
              regionToSkip = region.id
              openModal('modal-confirm-unskip-region')
            }}
          >
            <Broom /> unskip this piece</button
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
