<script>
    import IconButton from '@components/base/IconButton.svelte';

    import CornersOut from "phosphor-svelte/lib/CornersOut";

    export let action;
    export let style = "tool-ui";
</script>

<IconButton {style} title="Go to full extent" action={action}>
    <CornersOut />
</IconButton>