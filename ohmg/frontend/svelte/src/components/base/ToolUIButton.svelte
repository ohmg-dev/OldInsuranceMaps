<script>
    export let action;
    export let title;
    export let disabled = false;
    export let onlyIcon = true;

    export let type = "primary";

    let classStr = `button is-${type} is-small is-icon`;
    let spanStr = "is-small"

    if (onlyIcon) {
        spanStr = spanStr + ' icon'
    }

</script>

<button class="{classStr}" on:click={action} {title} {disabled}>
    <span class="{spanStr}">
        <slot></slot>
    </span>
</button>
