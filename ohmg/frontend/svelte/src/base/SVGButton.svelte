<script>
    import SvgIcon from "./SVGIcon.svelte";

    export let action;
    export let title;
    export let style;
    export let icon = null;
    export let disabled = false;
    export let size = "";

</script>

<button class="svg-btn {style}" on:click={action} {title} {disabled}>
    <slot></slot>
    <SvgIcon {icon} {size}/>
</button>

<style>
    :global(button.svg-btn > i) {
        background: #2c689c;
    }

    :global(button.svg-btn:hover > i) {
        background: #1b4060;
    }

    :global(button.svg-btn:disabled > i) {
        background: grey;
    }

    button {
        display: flex;
        align-items: center;
        vertical-align: middle;
        background: none;
        border: none;
        color: #2c689c
    }

    button:hover {
        color: #1b4060
    }

    button:disabled {
        cursor: default;
        color: gray;
    }

</style>