<script>
    import Scissors from "phosphor-svelte/lib/Scissors";
	import CheckSquareOffset from "phosphor-svelte/lib/CheckSquareOffset";

    import {getModal} from '@/base/Modal.svelte';
    import LoadingEllipsis from '@/base/LoadingEllipsis.svelte';

	import Link from '@/base/Link.svelte';

    import BaseCard from "./BaseCard.svelte";

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

</script>

<BaseCard>
    <div slot="card-top">
        <p>
            {#if document.file}
            <Link href={document.urls.resource} title={document.title}>{document.nickname}</Link>
            {:else}
            {document.nickname}
            {/if}
        </p>
    </div>
    <div slot="card-middle">
        {#if document.urls.thumbnail}
        <button class="thumbnail-btn" on:click={() => {
            modalLyrUrl=document.urls.image;
            modalExtent=[0, -document.image_size[1], document.image_size[0], 0];
            modalIsGeospatial=false;
            getModal('modal-simple-viewer').open();
            reinitModalMap = [{}];
            }} >
            <img style="cursor:zoom-in"
                src={document.urls.thumbnail}
                alt="{document.title}"
                />
        </button>
        {:else if document.iiif_info}
        <div style="text-align:center;">
            <img
                style="filter:opacity(75%)"
                src={document.iiif_info.replace("info.json", "full/,200/0/default.jpg")}
                alt="{document.title}"
                />
        </div>
        {:else}
        <div style="text-align:center;">{document.page_number}</div>
        {/if}
    </div>
    <div slot="card-bottom">
        {#if document.loading_file}
        <ul>
            <li>loading <LoadingEllipsis small={true}/></li>
            {#if CONTEXT.user.is_authenticated}
                <button
                class="is-text-link"
                on:click={() => {
                    document.loading_file = true;
                    postLoadDocument(document.id)
                }} >
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
                    postLoadDocument(document.id)
                }} >
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
            <li><button
                    class="is-text-link"
                    title="This document does not need to be split"
                    on:click={() => {
                        splitDocumentId = document.id;
                        getModal('modal-confirm-no-split').open()
                    }}>
                    <CheckSquareOffset/> no split needed
                </button>
            </li>
            <li><Link href={`/split/${document.id}`} title="Split this document">
                <Scissors/> split this document</Link></li>
            {#if CONTEXT.user.is_staff}
            <li><button
                    class="is-text-link"
                    disabled={documentsLoading}
                    on:click={() => {
                        document.loading_file = true;
                        postLoadDocument(document.id)
                    }} >
                    force reload document
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
