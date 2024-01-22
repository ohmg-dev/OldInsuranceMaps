<script>
    import IconButton from '@components/base/IconButton.svelte';

    import CornersOut from "phosphor-svelte/lib/CornersOut";

    export let action;
</script>

<IconButton style="tool-ui" title="Go to full extent" action={action}>
    <CornersOut />
</IconButton>