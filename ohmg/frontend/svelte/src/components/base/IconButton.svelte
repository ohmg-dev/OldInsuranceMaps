<script>
    import ArrowsClockwise from "phosphor-svelte/lib/ArrowsClockwise";
    import Article from "phosphor-svelte/lib/Article";
    import Crop from "phosphor-svelte/lib/Crop";
    import Link from "phosphor-svelte/lib/Link";
    import Lock from "phosphor-svelte/lib/Lock";
    import LockOpen from "phosphor-svelte/lib/LockOpen";
    import Question from "phosphor-svelte/lib/Question";
    import Trash from "phosphor-svelte/lib/Trash";
    import Wrench from "phosphor-svelte/lib/Wrench";
    import X from "phosphor-svelte/lib/X";
    import Check from "phosphor-svelte/lib/Check";
    import CaretDoubleRight from "phosphor-svelte/lib/CaretDoubleRight";
    import CaretDoubleLeft from "phosphor-svelte/lib/CaretDoubleLeft";

    import SvgIcon from "./SVGIcon.svelte";

    import IconContext from "phosphor-svelte/lib/IconContext";
    import { iconProps } from "@lib/utils"

    export let action;
    export let title;
    export let style;
    export let icon = null;
    export let disabled = false;
    export let size = "";

    if (style === "lite") {
        iconProps.weight = 'regular'
    }
</script>

<IconContext values={iconProps}>
    <button class={style} on:click={action} {title} {disabled}>
        {#if icon === "article"}
        <Article />
        {:else if icon === "refresh"}
        <ArrowsClockwise />
        {:else if icon === "trash"}
        <Trash />
        {:else if icon === "crop"}
        <Crop />
        {:else if icon === "link"}
        <Link />
        {:else if icon === "lock"}
        <Lock />
        {:else if icon === "lock-open"}
        <LockOpen />
        {:else if icon === "question"}
        <Question />
        {:else if icon === "wrench"}
        <Wrench />
        {:else if icon === "check"}
        <Check />
        {:else if icon === "caret-double-left"}
        <CaretDoubleLeft />
        {:else if icon === "caret-double-right"}
        <CaretDoubleRight />
        {:else if icon === "x"}
        <X />
        {:else if icon === "magnifier"}
        <SvgIcon icon="magnifier" {size}/>
        {/if}
        <slot></slot>
    </button>
</IconContext>

<style>
    button {
        display: flex;
        align-items: center;
        vertical-align: middle;
    }

    button:disabled {
        cursor: default;
    }
    
    button.lite {
        background: none;
        border: none;
        color:#2c689c;
        font-size: 1.7em;
    }
    button.lite:hover {
        color:#123B4F;
    }
    button.lite:disabled {
        color: grey;
    }
    
    button.lite-sm {
        background: none;
        border: none;
        color:#2c689c;
    }
    button.lite-sm:hover {
        color:#123B4F;
    }

    button.tool-ui {
        border-radius: 4px;
        font-size: 19.2px;
        color: #1b4060;
        height: 30px;
        color: white;
        background: #1b4060;
    }

    button.tool-ui:hover {
        background: #2c689c;
        color:white;
    }

    button.tool-ui-secondary {
        border-radius: 4px;
        font-size: 19.2px;
        color: #1b4060;
        height: 30px;
    }

    button.tool-ui-secondary:disabled {
        color: darkslategrey;
        background: lightgrey;
        cursor: default;
    }

    button.link {
        color: #2c689c;
        background: none;
        border: none;
        display: inline;
        vertical-align: unset;
        padding: 0;
    }

    button.link:hover {
        text-decoration: underline;
    }

    button.nav-link {
        color: white;
        background: none;
        border: none;
        display: inline;
        padding: 0;
    }

    button.nav-link:hover {
        text-decoration: underline;
    }

</style>