<script>
  import { TableSort } from 'svelte-tablesort';
  import Link from '../common/Link.svelte';
  import LoadingEllipsis from '../common/LoadingEllipsis.svelte';

  import { getFromAPI } from '../../lib/requests';

  export let CONTEXT;

  let all_places = [];
  let items = [];
  let loading = true;

  getFromAPI('/api/beta2/places/', CONTEXT.ohmg_api_headers, (result) => {
    all_places = result;
    items = result;
    loading = false;
  });

  function updateFilteredList(filterText) {
    if (filterText && filterText.length > 0) {
      items = [];
      all_places.forEach(function (place) {
        const placeName = place.display_name.toUpperCase();
        const filterBy = filterText.toUpperCase();
        if (placeName.indexOf(filterBy) > -1) {
          items.push(place);
        }
      });
    } else {
      items = all_places;
    }
  }
  let filterInput;
  $: updateFilteredList(filterInput);
</script>

<div>New! <Link href="/united-states" title="Place search">Search by place hierarchy &rarr;</Link></div>
<div class="filter-container">
  <input type="text" id="filterInput" placeholder="Filter by place name..." bind:value={filterInput} />
</div>
<div style="overflow-x:auto;">
  {#if loading}
    <div style="text-align:center;">
      <LoadingEllipsis />
    </div>
  {:else if items.length === 0}
    <p><em>No places found...</em></p>
  {:else}
    <TableSort {items}>
      <tr slot="thead">
        <th data-sort="name" style="max-width:300px;" title="Name of mapped location">Place</th>
        <th data-sort="sort_years" style="max-width:300px;" title="Volumes available">Volumes available</th>
      </tr>
      <tr slot="tbody" let:item={p} style="height:38px;">
        <td><Link title="View all {p.name} mosaics in viewer" href={p.url}>{p.display_name}</Link></td>
        <td
          >{#each p.maps as v, i}<Link href="/map/{v.identifier}"
              >{v.year}{#if v.volume_number}, Vol. {v.volume_number}{/if}</Link
            >{#if i < p.maps.length - 1},
            {/if}{/each}</td
        >
      </tr>
    </TableSort>
  {/if}
</div>

<style>
  .filter-container {
    padding: 0px 10px 10px 10px;
  }

  .filter-container > input {
    width: 100%;
  }
</style>
