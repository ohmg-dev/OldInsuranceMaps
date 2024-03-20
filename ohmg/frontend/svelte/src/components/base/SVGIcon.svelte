<script>
    export let icon;
    export let size = 'lg';
    export let link = '';
</script>

<i class="i-{icon} i-{icon}-{size}{link == "enabled" ? ' link-enabled' : ''}{link == "disabled" ? ' link-disabled' : ''}"></i>

<style>
    * {
        --volume-svg: url(/static/icons/noun_UprightBook_2089467.svg);
        --volume2-svg: url(/static/icons/noun-book-3124501-FFFFFF.svg);
        --volume-size: 65px;
        --document-svg: url(/static/icons/noun_Scroll_2592600.svg);
        --document-size: 70px;
        --layer-svg: url(/static/icons/noun_Layer_2583171.svg);
        --layer-size: 75px;
        --webmap-svg: url(/static/icons/noun_FoldedMap_2592599.svg);
        --webmap-size: 70px;
        --pinmap-svg: url(/static/icons/noun_pinmap_1832932.svg);
        --pinmap-size: 70px;
        --user-svg: url(/static/icons/noun_User_1236015.svg);
        --user-size: 50px;
        --magnifier-svg: url(/static/icons/noun-magnifier-858462.svg);
        --magnifier-size: 55px;
        --pin-svg: url(/static/icons/noun-map-pin-858464.svg);
        --pin-size: 55px;
        --compass-svg: url(/static/icons/noun-compass-867471.svg);
        --compass-size: 55px;
        --camera-svg: url(/static/icons/noun-camera-858458.svg);
        --camera-size: 60px;
    }

    i {
        display: inline-block;
        background: black;
        mask-size: cover;
        -webkit-mask-size: cover;
    }

    .i-magnifier {
        mask-image: var(--magnifier-svg);
        -webkit-mask-image: var(--magnifier-svg);
    }
    .i-magnifier-lg {
        width: 55px;
        height: 55px;
    }
    .i-magnifier-md {
        width: calc(var(--pin-size)*.7);
        height: calc(var(--pin-size)*.7);
    }
    .i-magnifier-sm {
        width: calc(var(--pin-size)*.55);
        height: calc(var(--pin-size)*.55);
    }

    .i-pin {
        mask-image: var(--pin-svg);
        -webkit-mask-image: var(--pin-svg);
    }
    .i-pin-lg{
        width: var(--pin-size);
        height: var(--pin-size);
    }
    .i-pin-md {
        width: calc(var(--pin-size)*.7);
        height: calc(var(--pin-size)*.7);
    }
    .i-pin-sm {
        width: calc(var(--pin-size)*.55);
        height: calc(var(--pin-size)*.55);
    }

    .i-compass {
        mask-image: var(--compass-svg);
        -webkit-mask-image: var(--compass-svg);
    }
    .i-compass-lg{
        width: var(--compass-size);
        height: var(--compass-size);
    }
    .i-compass-md {
        width: calc(var(--compass-size)*.7);
        height: calc(var(--compass-size)*.7);
    }
    .i-compass-sm {
        width: calc(var(--compass-size)*.55);
        height: calc(var(--compass-size)*.55);
    }

    .i-volume {
        mask-image: var(--volume2-svg);
        -webkit-mask-image: var(--volume2-svg);
    }
    .i-volume-lg{
        width: var(--volume-size);
        height: var(--volume-size);
    }
    .i-volume-md {
        width: calc(var(--volume-size)*.7);
        height: calc(var(--volume-size)*.7);
    }
    .i-volume-sm {
        width: calc(var(--volume-size)*.55);
        height: calc(var(--volume-size)*.55);
    }

    .i-document {
        mask-image: var(--document-svg);
        -webkit-mask-image: var(--document-svg);
    }
    .i-document-lg {
        width: var(--document-size);
        height: var(--document-size);
    }
    .i-document-md {
        width: calc(var(--document-size)*.7);
        height: calc(var(--document-size)*.7);
    }
    .i-document-sm {
        width: calc(var(--document-size)*.55);
        height: calc(var(--document-size)*.55);
    }

    .i-layer {
        mask-image: var(--layer-svg);
        -webkit-mask-image: var(--layer-svg);
    }
    .i-layer-lg {
        width: var(--layer-size);
        height: var(--layer-size);
    }
    .i-layer-md {
        width: calc(var(--layer-size)*.7);
        height: calc(var(--layer-size)*.7);
    }
    .i-layer-sm {
        width: calc(var(--layer-size)*.55);
        height: calc(var(--layer-size)*.55);
    }

    .i-webmap {
        mask-image: var(--webmap-svg);
        -webkit-mask-image: var(--webmap-svg);
    }
    .i-webmap-lg {
        width: var(--webmap-size);
        height: var(--webmap-size);
    }
    .i-webmap-md {
        width: calc(var(--webmap-size)*.7);
        height: calc(var(--webmap-size)*.7);
    }
    .i-webmap-sm {
        width: calc(var(--webmap-size)*.55);
        height: calc(var(--webmap-size)*.55);
    }

    .i-pinmap {
        mask-image: var(--pinmap-svg);
        -webkit-mask-image: var(--pinmap-svg);
    }
    .i-pinmap-lg {
        width: var(--pinmap-size);
        height: var(--pinmap-size);
    }
    .i-pinmap-md {
        width: calc(var(--pinmap-size)*.7);
        height: calc(var(--pinmap-size)*.7);
    }
    .i-pinmap-sm {
        width: calc(var(--pinmap-size)*.55);
        height: calc(var(--pinmap-size)*.55);
    }

    .i-user {
        mask-image: var(--user-svg);
        -webkit-mask-image: var(--user-svg);
    }
    .i-user-lg {
        width: var(--user-size);
        height: var(--user-size);
    }
    .i-user-md {
        width: calc(var(--user-size)*.7);
        height: calc(var(--user-size)*.7);
    }
    .i-user-sm {
        width: calc(var(--user-size)*.55);
        height: calc(var(--user-size)*.55);
    }

    .i-camera {
        mask-image: var(--camera-svg);
        -webkit-mask-image: var(--camera-svg);
    }
    .i-camera-lg {
        width: var(--camera-size);
        height: var(--camera-size);
    }
    .i-camera-md {
        width: calc(var(--camera-size)*.7);
        height: calc(var(--camera-size)*.7);
    }
    .i-camera-sm {
        width: calc(var(--camera-size)*.55);
        height: calc(var(--camera-size)*.55);
    }

</style>