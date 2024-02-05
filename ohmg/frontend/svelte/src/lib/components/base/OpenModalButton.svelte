<script>
    import IconButton from "./IconButton.svelte";
    import {getModal} from "./Modal.svelte"

    export let modalId;
    export let title = "More info";
    export let style = "lite";
    export let icon = "question";
</script>

<IconButton {style} {icon} action={() => {getModal(modalId).open()}} title={title}>
    <slot></slot>
</IconButton>
