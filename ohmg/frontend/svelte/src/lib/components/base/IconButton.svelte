<script>
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

    import IconContext from "phosphor-svelte/lib/IconContext";
    import { iconProps } from "@helpers/utils"

    export let action;
    export let title;
    export let style;
    export let icon = null;
    export let disabled = false;

    if (style === "lite") {
        iconProps.weight = 'regular'
    }
</script>

<IconContext values={iconProps}>
    <button class={style} on:click={action} title={title} disabled={disabled}>
        {#if icon === "article"}
        <Article />
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
        {:else if icon === "x"}
        <X />
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

    button.lite {
        background: none;
        border: none;
        color:#2c689c;
        font-size: 1.7em;
    }
    button.lite:hover {
        color:#123B4F;
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
</style>