<script>
import '../css/shared.css';
import MarkdownPage from './components/MarkdownPage.svelte'

const source = `There are a few different ways to interact with this platform, and this page will offer a quick overview for all of them, as well as links out to more detailed information. If you need any help, do not hesitate to get in touch. Thanks!

## Finding and Viewing Maps

**Search by Place** - Each fire insurance map atlas is attached to a locale, generally a city or town. Find your locale of interest by [searching the map](/browse/#map), and then go to the Viewer for that locale. You can also [search by place name](browse/#places), or [explore places as a hierarchy](/united-states) (this latter option works but is still in development).

**Search by Item** - You can also [search all items](/browse/#items) individually, which is the quickest way to access the summary page for each one, showing its georeferencing progress.

## Contributing Work

Hooray! You've created an account and are ready to get started! The workflow is very structured and hierarchical, based on two levels of content: items (Sanborn map editions, or "volumes") and resources (pages or "sheets" within a given volume).

The entry point for georeferencing is an item, so start by [finding an item](/browse#items), and going to its summary page.

### Item-level management

Here is a recommended approach for creating a mosaic from a given edition or volume.

1. 

### Georeferencing Individual Resources

T

The system is organized with two high-level entities: Items and Places. Items are Sanborn map editions, or individual volumes of multi-part atlases, with a one-to-one relationship to items in the LOC collection. Each item is attached to one or more Places, the latter being a 


Places are heirarchical geographical boundaries, state, county, city, etc.--and each Item is a Sanborn map edition or volume attached to one or more Places.

`

</script>

<main>
	<MarkdownPage title={"Getting Started"} source={source} />
	
	<h2>Collaborations</h2>
	<div class="collab-tile">
		<div style="display:flex; justify-content:left; align-items:center;">
			<img height=30 width=30 src="https://www.openhistoricalmap.org/assets/osm_logo-796d69930b9f9f0fb3aa93152588ad4a2719ffd0b1e321d6045bf343a44e863e.png" />
			<h4><a href="https://www.openhistoricalmap.org">OpenHistoricalMap</a></h4>
		</div>
		<div>
			OHM is an OpenStreetMap-inspired project, where contributors can add historical features from anywhere in the world. Any georeferenced historical maps on OldInsuranceMaps.net can be easily integrated as basemaps in the OHM editor, so that features can be digitized directly from them.
		</div>
	</div>
</main>

<style>

main {
	display: flex;
	flex-direction: column;
}

</style>
