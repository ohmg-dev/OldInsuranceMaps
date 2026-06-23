<script>
    import Modal, { openModal } from '../../base/Modal.svelte';
    import Copy from 'phosphor-svelte/lib/Copy';
    import {copyToClipboard} from "../../../lib/utils";

    export let text;
    export let label = "";

    const elementId = window.crypto.randomUUID()
    const modalId = `modal-${elementId}`
</script>

<Modal id={modalId}>
    <p>The following text has been copied to your clipboard:</p>
    <p class="report-copied">{text}</p>
</Modal>
<input
    id={elementId}
    type="hidden"
    value={text}
/>
<button class={label ? '' : 'text-as-label'} on:click={() => {
    copyToClipboard(elementId);
    openModal(modalId)
}}>{label ? label : text} <Copy/></button>

<style>
    button {
        text-decoration: none;
        background: none;
        border: none;
        color: var(--theme-highlight-color);
    }
    button.text-as-label {
        font-family: mono;
        font-size: 0.9em;
        text-align: start;
    }
    .report-copied {
        background:rgb(245,245,245);
        padding:5px;
        font-family: mono;
    }
</style>