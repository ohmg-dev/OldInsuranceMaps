<script>
    export let title;
    export let actions = false;
</script>

<dt class={actions ? 'actions' : ''}>{title}</dt>

<style>
    dt {
        padding: .25em .5em;
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        font-weight: 700;
        font-size: .85em;
        background-color: rgb(188, 241, 253);
    }
    dt.actions {
        background-color: rgb(253, 195, 188);
    }
</style>