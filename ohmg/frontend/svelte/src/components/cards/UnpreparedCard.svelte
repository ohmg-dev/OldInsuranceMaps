<script>
  import Scissors from 'phosphor-svelte/lib/Scissors';
  import Square from 'phosphor-svelte/lib/Square';
  import CheckSquare from 'phosphor-svelte/lib/CheckSquare';
  import CheckSquareOffset from 'phosphor-svelte/lib/CheckSquareOffset';
  import ArrowClockwise from 'phosphor-svelte/lib/ArrowClockwise';

  import { getModal } from '../modals/BaseModal.svelte';

  import Link from '../common/Link.svelte';
  import LoadingEllipsis from '../common/LoadingEllipsis.svelte';

  import BaseCard from './BaseCard.svelte';

  export let CONTEXT;
  export let document;
  export let sessionLocks;
  export let userCanEdit;
  export let modalLyrUrl;
  export let modalExtent;
  export let modalIsGeospatial;
  export let reinitModalMap;
  export let postLoadDocument;
  export let splitDocumentId;
  export let documentsLoading;
  export let bulkPreparing;
  export let bulkPrepareList;

  $: bulkPrepare = bulkPrepareList.includes(document.id);

  function handleChange() {
    bulkPrepare = !bulkPrepare;
    if (bulkPrepare) {
      bulkPrepareList = bulkPrepareList.concat([document.id]);
    } else {
      bulkPrepareList = bulkPrepareList.filter((id) => id !== document.id);
    }
  }
</script>

<BaseCard>
  <div slot="card-top">
    {#if document.file}
      <Link href={document.urls.resource} title={document.title}>{document.nickname}</Link>
    {:else}
      {document.nickname}
    {/if}
  </div>
  <div slot="card-middle">
    {#if document.urls.thumbnail}
      <button
        class="thumbnail-btn"
        on:click={() => {
          modalLyrUrl = document.urls.image;
          modalExtent = [0, -document.image_size[1], document.image_size[0], 0];
          modalIsGeospatial = false;
          getModal('modal-simple-viewer').open();
          reinitModalMap = [{}];
        }}
      >
        <img style="cursor:zoom-in" src={document.urls.thumbnail} alt={document.title} />
      </button>
    {:else if document.iiif_info}
      <div style="text-align:center;">
        <img
          style="filter:opacity(75%)"
          src={document.iiif_info.replace('info.json', 'full/,200/0/default.jpg')}
          alt={document.title}
        />
      </div>
    {:else}
      <div style="text-align:center;">{document.page_number}</div>
    {/if}
  </div>
  <div slot="card-bottom">
    {#if document.loading_file}
      <ul>
        <li>loading <LoadingEllipsis small={true} /></li>
        {#if CONTEXT.user.is_authenticated}
          <button
            class="is-text-link"
            on:click={() => {
              document.loading_file = true;
              postLoadDocument(document.id);
            }}
          >
            restart load
          </button>
        {/if}
      </ul>
    {:else if !document.file}
      <ul>
        <li>
          {#if CONTEXT.user.is_authenticated}
            <button
              class="is-text-link"
              disabled={documentsLoading}
              on:click={() => {
                document.loading_file = true;
                postLoadDocument(document.id);
              }}
            >
              load document
            </button>
          {:else}
            not yet loaded
          {/if}
        </li>
      </ul>
    {:else if sessionLocks.docs[document.id]}
      <ul style="text-align:center">
        <li><em>preparation in progress...</em></li>
        <li><em>user: {sessionLocks.docs[document.id].user.username}</em></li>
      </ul>
    {:else if userCanEdit}
      <ul>
        <li>
          {#if bulkPreparing}
            <button class="is-text-link" title="This document does not need to be split" on:click={handleChange}>
              {#if bulkPrepare}
                <CheckSquare />
              {:else}
                <Square />
              {/if}
              no split needed
            </button>
          {:else}
            <button
              class="is-text-link"
              title="This document does not need to be split"
              on:click={() => {
                splitDocumentId = document.id;
                getModal('modal-confirm-no-split').open();
              }}
            >
              <CheckSquareOffset /> no split needed
            </button>
          {/if}
        </li>
        <li>
          <Link href={`/split/${document.id}`} title="Split this document">
            <Scissors /> split this document</Link
          >
        </li>
        {#if CONTEXT.user.is_staff}
          <li>
            <button
              class="is-text-link"
              disabled={documentsLoading}
              on:click={() => {
                document.loading_file = true;
                postLoadDocument(document.id);
              }}
            >
              <ArrowClockwise /> force reload
            </button>
          </li>
        {/if}
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
