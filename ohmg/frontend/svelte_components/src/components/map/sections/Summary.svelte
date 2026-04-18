<script>
  import Link from '../../common/Link.svelte';
  import DownloadSectionModal from '../../modals/ItemDownloadSectionModal.svelte';
  import InfoModalButton from '../../buttons/InfoModalButton.svelte';

  import Sessions from '../../tables/Sessions.svelte';
  import MapContributors from '../../tables/MapContributors.svelte';

  import TabbedSection from '../../base/TabbedSection.svelte';

  export let CONTEXT;
  export let MAP;
  export let SESSION_SUMMARY;
  export let LAYERSETS = [];

  const tabs = [
    {id: "details", title: "Details"},
    {id: "stats", title: "Stats"},
    {id: "activity", title: "Activity"},
  ]
  let activeTab = tabs[0].id
</script>

<DownloadSectionModal id={'download-section-modal'} />
<section>
  <TabbedSection {tabs} bind:activeTab >
    <div>
      {#if activeTab == 'details'}
        <div class="fixed-grid has-12-cols has-1-cols-mobile">
          <div class="grid">
            <div class="cell is-col-span-5">
              <h3>Record</h3>
              <table>
                <tbody>
                  <tr>
                    <td>Title</td>
                    <td>Sanborn Map of {MAP.title}</td>
                  </tr>
                  <tr>
                    <td>Year</td>
                    <td>{MAP.year}</td>
                  </tr>
                  <tr>
                    <td>Locale</td>
                    <td><Link href="/{MAP.locale.slug}">{MAP.locale.display_name}</Link></td>
                  </tr>
                  <tr>
                    <td>Source</td>
                    <td
                      ><Link href="https://loc.gov/item/{MAP.identifier}" external={true}
                        >loc.gov/item/{MAP.identifier}</Link
                      ></td
                    >
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="cell is-col-span-7">
              <h3>Contributors & Attribution</h3>
              <table>
                <thead>
                  <tr>
                    <td>Initial load</td>
                    <td>
                      {#if MAP.progress.loaded_pages}
                        loaded by <Link href={MAP.loaded_by.profile}>{MAP.loaded_by.name}</Link> - {MAP.loaded_by.date}<br
                        />
                      {:else}--{/if}
                    </td>
                  </tr>
                  <tr>
                    <td>Prep</td>
                    <td>
                      {SESSION_SUMMARY.prep_ct} document{#if SESSION_SUMMARY.prep_ct != 1}s{/if} prepared{#if SESSION_SUMMARY.prep_ct > 0}&nbsp;by
                        {#each SESSION_SUMMARY.prep_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.prep_contributors.length - 1},
                          {/if}{/each}{/if}
                    </td>
                  </tr>
                  <tr>
                    <td>Georef</td>
                    <td>
                      {SESSION_SUMMARY.georef_ct} georeferencing session{#if SESSION_SUMMARY.georef_ct != 1}s{/if}{#if SESSION_SUMMARY.georef_ct > 0}&nbsp;by
                        {#each SESSION_SUMMARY.georef_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.georef_contributors.length - 1},
                          {/if}{/each}{/if}
                    </td>
                  </tr>
                  <tr>
                    <td>Credit line:</td>
                    <td>Library of Congress, Geography and Map Division, Sanborn Maps Collection.</td>
                  </tr>
                </thead>
              </table>
            </div>
          </div>
        </div>
      {:else if activeTab == 'stats'}
        <div style="margin-top:10px;">
          <p>
            These users have contributed to the creation of the content within this map, by preparing or georeferencing
            images. Currently, trimming or "multimask" work is not reflected in this table.
          </p>
        </div>
        <MapContributors {CONTEXT} mapId={MAP.identifier} />
      {:else if activeTab == 'activity'}
        <div style="margin-top:10px;">
          <p>
            Below is complete record of all preparation or georeferencing actions that have been performed on documents
            within this map. Currently, trimming or "multimask" work is not reflected in this table.
          </p>
        </div>
        <Sessions {CONTEXT} mapFilter={{ id: MAP.identifier }} showMap={false} paginate={true} limit="50" />
      {/if}
    </div>
  </TabbedSection>
</section>

<style>
  table {
    width: 100%;
    border: 1px solid #ddd;
    border-radius: 4px;
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  td {
    padding: 4px;
  }

  td {
    background-color: #ffffff;
    width: 100%;
  }
  td:first-child {
    background-color: #f6f6f6;
    font-weight: 800;
    width: 150px;
  }
</style>
