<script>
    import Modal from "@components/base/Modal.svelte";
    import Link from "@components/base/Link.svelte";

    export let viewerUrl = "";
    export let placeName = "";
    export let id;
</script>

<Modal id={id}>
    <h3>Mosaic Preview</h3>
	<p>The <strong>Mosaic Preview</strong> shows progress toward a full mosaic of this item's content&mdash;as documents are georeferenced, they will automatically appear here.</p>
	<p>You can also view this mosaic alongside all other mosaics for this locale: <Link href={viewerUrl} external={true} title={"Open viewer for " + placeName}>{placeName}</Link></p>
</Modal>