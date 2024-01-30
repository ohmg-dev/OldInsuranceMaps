<script>
	import IconContext from 'phosphor-svelte/lib/IconContext';
	import Link from "@components/base/Link.svelte";
	import { iconProps } from "@helpers/utils"

	const linkSets =[
		{
			"header": "Content",
			"links": [
				{
					"title": "Search Maps",
					"href": "/browse",
					"external": false,
				},
				{
					"title": "Contributors",
					"href": "/profiles",
					"external": false,
				},
				{
					"title": "GitHub",
					"href": "https://github.com/mradamcox/ohmg",
					"external": true,
				},
			]
		},
		{
			"header": "Learn More",
			"links": [
				{
					"title": "FAQ",
					"href": "/faq",
					"external": false,
				},
				{
					"title": "About Sanborn Maps",
					"href": "/about-sanborn-maps",
					"external": false,
				},
				{
					"title": "Documentation",
					"href": "https://ohmg.dev/docs",
					"external": true,
				},
			]
		},
		{
			"header": "News & Updates",
			"links": [
				{
					"title": "FAQ",
					"href": "/faq",
					"external": false,
				},
				{
					"title": "Contact",
					"href": "/contact",
					"external": false,
				},
				{
					"title": "Blog",
					"href": "https://ohmg.dev/blog",
					"external": true,
				},
			]
		},
	]
</script>

<IconContext values={iconProps} >
<footer class="lahmg-footer">
	<div class="main-row">
		{#each linkSets as set}
		<div>
			<h4>{set.header}</h4>
			<ul>
				{#each set.links as link}
				<li><Link href={link.href} classes={["white"]} title={link.title} external={link.external}>{link.title}</Link></li>
				{/each}
			</ul>
		</div>
		{/each}
	</div>
	<div style="color:lightgrey; text-align:right;">
		Copyright © 2024
	</div>
</footer>
</IconContext>
<style>
	footer {
		display: flex;
		flex-direction: column;
		background:#123B4F;
		color: white;
		padding: 15px;
		font-weight: 500;
		min-height: 190px;
	}
	.main-row {
		display: flex;
		flex-direction: row;
		justify-content: space-around;
	}	
	footer > div {
		margin: 0px 10px;
	}

	ul {
		padding: 0;
		margin: 0;
		list-style: none;
	}
	
	@media only screen and (max-width: 480px) {
		.main-row {
			flex-direction: column;
		}
	}
</style>
