<script>
    import Broom from "phosphor-svelte/lib/Broom";

    import {getModal} from '../modals/BaseModal.svelte';

	import Link from '../common/Link.svelte';

    import BaseCard from "./BaseCard.svelte";

    export let region;
    export let sessionLocks;
    export let userCanEdit;
    export let modalLyrUrl;
    export let modalExtent;
    export let modalIsGeospatial;
    export let reinitModalMap;
    export let postSkipRegion;

</script>

<BaseCard>
    <div slot="card-top">
        <Link href={region.urls.resource} title={region.title}>{region.nickname}</Link>
    </div>
    <div slot="card-middle">
        <button class="thumbnail-btn" on:click={() => {
            modalLyrUrl=region.urls.image;
            modalExtent=[0, -region.image_size[1], region.image_size[0], 0];
            modalIsGeospatial=false;
            getModal('modal-simple-viewer').open();
            reinitModalMap = [{}];
            }} >
            <img style="cursor:zoom-in"
                src={region.urls.thumbnail}
                alt={region.title}
                />
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
                title="click to move this document to the non-map section"
                on:click={() => {postSkipRegion(region.id, false)}}>
                <Broom /> unskip this piece</button>
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
