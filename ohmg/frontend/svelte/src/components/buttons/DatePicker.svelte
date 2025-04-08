<script>
  import { DatePicker } from '@svelte-plugins/datepicker';
  import { format } from 'date-fns';
  import X from 'phosphor-svelte/lib/X';

  const today = new Date();

  const MILLISECONDS_IN_DAY = 24 * 60 * 60 * 1000;

  const getDateFromToday = (days) => {
    return Date.now() - days * MILLISECONDS_IN_DAY;
  };

  export let startDate = '';
  export let endDate = '';
  let dateFormat = 'MMM d, yyyy';
  let isOpen = false;

  let formattedStartDate = '';

  const onClearDates = () => {
    startDate = '';
    endDate = '';
  };

  const toggleDatePicker = () => (isOpen = !isOpen);
  const formatDate = (dateString) => (dateString && format(new Date(dateString), dateFormat)) || '';

  $: formattedStartDate = formatDate(startDate);
  $: formattedEndDate = formatDate(endDate);
</script>

<div class="date-filter">
  <DatePicker bind:isOpen bind:startDate bind:endDate isRange showPresets>
    <button class="date-field" on:click={toggleDatePicker} class:open={isOpen}>
      <div class="date">
        {#if startDate}
          {formattedStartDate} - {formattedEndDate}
        {:else}
          Filter by date range...
        {/if}
        {#if startDate}
          <button on:click={onClearDates}>
            <X />
          </button>
        {/if}
      </div>
    </button>
  </DatePicker>
</div>

<style>
  .date-field {
    align-items: center;
    background-color: #fff;
    border-bottom: 1px solid #e8e9ea;
    display: inline-flex;
    gap: 8px;
    min-width: 100px;
    padding: 8px 16px;
    border-radius: 5px;
    border: solid rgb(197, 208, 219) 0.5px;
  }

  .date-field.open {
    border-bottom: 1px solid #0087ff;
  }

  .date {
    font-size: 16px;
    color: rgb(126, 137, 148);
  }
</style>
