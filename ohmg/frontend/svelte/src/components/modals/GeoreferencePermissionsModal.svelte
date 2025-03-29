<script>
    import Modal from "./BaseModal.svelte"
    export let id;
    export let user;
    export let userCanEdit;
    export let item;
</script>

<Modal id={id}>
    <h3>Access Settings</h3>
    <p>Access level: {item.access}</p>
    <p><em>
        {#if item.access == "none"}
        Only admins can georeference this item's content.
        {:else if item.access == "sponsor"}
        Only users linked to this item's sponsor can georeference it's content.
        {:else if item.access == "any"}
        Any logged in users can georeference this item's content.
        {/if}
    </em></p>

        {item.status}
        {item.sponsor}

        {user}
        {userCanEdit}
</Modal>