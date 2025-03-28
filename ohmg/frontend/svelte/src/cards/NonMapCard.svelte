<script>
    import MapTrifold from "phosphor-svelte/lib/MapTrifold";

    import {getModal} from '@/base/Modal.svelte';

	import Link from '@/base/Link.svelte';

    import BaseCard from "./BaseCard.svelte";

    export let nonmap;
    export let userCanEdit;
    export let modalLyrUrl;
    export let modalExtent;
    export let modalIsGeospatial;
    export let reinitModalMap;
    export let postRegionCategory;

</script>

<BaseCard>
    <div slot="card-top">
        <Link href={nonmap.urls.resource} title={nonmap.title}>{nonmap.nickname}</Link>
    </div>
    <div slot="card-middle">
        <button class="thumbnail-btn" on:click={() => {
            modalLyrUrl=nonmap.urls.image;
            modalExtent=[0, -nonmap.image_size[1], nonmap.image_size[0], 0];
            modalIsGeospatial=false;
            getModal('modal-simple-viewer').open();
            reinitModalMap = [{}];
            }} >
            <img style="cursor:zoom-in"
                src={nonmap.urls.thumbnail}
                alt={nonmap.title}
                />
        </button>
    </div>
    <div slot="card-bottom">
        {#if userCanEdit}
        <div>
            <ul>
                <li><button
                    class="is-text-link"
                    on:click={() => {postRegionCategory(nonmap.id, "map")}}
                    title="click to set this document back to 'prepared' so it can be georeferenced">
                    <MapTrifold /> this <em>is</em> a map
                </button></li>
            </ul>
        </div>
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
