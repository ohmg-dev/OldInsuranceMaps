<script>
    import { slide } from 'svelte/transition';
    import {slugify} from '../../lib/utils';

    import InfoModalButton from "../buttons/InfoModalButton.svelte";
    import ConditionalDoubleChevron from "../buttons/ConditionalDoubleChevron.svelte";

    export let TITLE;
    export let EXPANDED = false;
    export let DISABLED = false;
    export let INFO_MODAL_ID = "";
    export let IS_SUBSECTION = false;

</script>

<section class="{IS_SUBSECTION ? 'subsection' : ''}">
    <div class="section-title-bar">
        <button
            class="section-toggle-btn"
            title={EXPANDED ? 'Collapse section' : 'Expand section'}
            disabled={DISABLED}
            on:click={() => {
                EXPANDED = !EXPANDED;
            }}
        >
        <ConditionalDoubleChevron down={EXPANDED} />
        <a id={slugify(TITLE)} class="title-link">
            {#if !IS_SUBSECTION}
            <h2>{TITLE}</h2>
            {:else}
            <h3>{TITLE}</h3>
            {/if}
        </a>
        </button>
        {#if INFO_MODAL_ID}
            <InfoModalButton modalId={INFO_MODAL_ID} />
        {/if}
    </div>
    {#if EXPANDED}
        <div style="margin-bottom:10px;" transition:slide|global>
            <slot></slot>
        </div>
    {/if}
</section>


<style>
  .title-link {
    scroll-margin-top: 50px;
  }

  section {
    border-bottom: 1px solid rgb(149, 149, 149);
  }

  section.subsection {
    border-bottom: 1px dashed rgb(149, 149, 149);
  }

  button.section-toggle-btn {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    background: none;
    border: none;
    color: #2c689c;
    padding: 0;
  }

  button.section-toggle-btn,
  a {
    text-decoration: none;
  }

  button.section-toggle-btn:hover {
    color: #1b4060;
  }

  button.section-toggle-btn:disabled,
  button.section-toggle-btn:disabled > a {
    color: grey;
  }

  button:disabled {
    cursor: default;
  }

  button:disabled a {
    cursor: default;
  }

  .section-title-bar {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

</style>
