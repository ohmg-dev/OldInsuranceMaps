<script>
	import MarkdownPage from './components/MarkdownPage.svelte'
	
	const source = `
### Why ".net"?

Because the idea is to create a collaborative, public place (a network or "commons") rather than a commercial product or non-profit organization.

### How can I find a map of my house?

The best way to find a specific location is to

1. Go to the [Search](/search) page and find your city on the map.
2. Go to **Viewer** for your city.
3. Pan and zoom the map or, if you are currently in your house and on a phone, use the "locate me" button.

### How accurate are these maps?

This is a more complex question than it may seem at first. In general the original Sanborn maps were factually and spatially quite accurate (though not without quirks), but the way they are georeferenced and presented as overlays on this site can be quite inaccurate. This is because the ground control points created during the georeferencing process may not have been placed well, creating distortion or general misalignment of the maps.

*No attempt to calculate GCP error values has been made on this platform (yet).*

That said, you'll quickly see that even with slight misalignment in some places, these maps still provide a rich window into the historical fabric of the city.

### Why are there so many Louisiana maps?

The 2022 pilot project included a wide range of Sanborn editions across Louisiana, based on the following criteria:

- Include the earliest edition for every community, regardless of date.
- Include any editions published through 1910 for all communities outside of New Orleans.
- Include only the earliest full coverage of New Orleans (in four volumes, from 1885 to 1893).

Applied across the state, these criteria produce 268 volumes covering 138 communities, with a combined sheet count of over 1,600. Since then, of course, we have expanded coverage as requested by participants.

### How can I add more volumes?

Check through the [LOC collection](https://loc.gov/collections/sanborn-maps), and if you find an edition you would like to georeference (or get your techy friend to georeference for you), [fill out this form](https://docs.google.com/forms/d/e/1FAIpQLSeF6iQibKEsjIv4fiYIW4vVVxyimLL8sDLX4BLU7HSWsRBOFQ/viewform?usp=sf_link).

We are open to adding more items on an *ad hoc* basic (especially for smaller cities and towns).

If you or your organization would like to a large number of maps, like all your county or state, please [get in touch](/contact).

### Why are you using the term "volume"?

We are using this term somewhat imprecisely, because only Sanborn maps of large cities have proper "volumes" (see New Orleans 1885 vol. 1, 1885 vol. 2, 1887 vol. 3, and 1893 vol. 4). The vast majority of maps in the Sanborn collection may be better called "editions" (see Baton Rouge, 1885).

However, the hierarchy of the LOC collection handles editions and volumes at the same level, they are "items", so we decided "volume" would be a reasonable compromise for the sake of unity. Therefore, a volume is an atomic unit that contains one or more sheets.
`
</script>

<MarkdownPage source={source} title={"FAQ"} />
