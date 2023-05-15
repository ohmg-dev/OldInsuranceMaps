<script>
import Icon from 'svelte-icons-pack/Icon.svelte';
import FiExternalLink from 'svelte-icons-pack/fi/FiExternalLink';

export let USER;
</script>
<footer class="lahmg-footer">
	<div class="main-row">
		<div>
			<h4>Content</h4>
			<ul>
				<li><a href="/browse">Browse Maps</a></li>
				<li><a href="/people">Participants</a></li>
				<li><a href="https://github.com/mradamcox/loc-insurancemaps">GitHub <Icon src={FiExternalLink} /></a></li>
			</ul>
		</div>
		<div>
			<h4>Learn More</h4>
			<ul>
				<li><a href="https://ohmg.dev/faq">FAQ <Icon src={FiExternalLink} /></a></li>
				<li><a href="https://ohmg.dev/docs">Documentation <Icon src={FiExternalLink} /></a></li>
				<li><a href="https://ohmg.dev/docs/category/sanborn-maps-1">About Sanborn Maps <Icon src={FiExternalLink} /></a></li>
			</ul>
		</div>
		<div>
			<h4>News & Updates</h4>
			<ul>
				<li><a href="/newsletter/lahmg-news/archive" >Newsletter Archive</a></li>
				<li><a href="https://ohmg.dev/blog" >Blog <Icon src={FiExternalLink} /></a></li>
				<li><a href="/#contact" >Contact <Icon src={FiExternalLink} /></a></li>
			</ul>
		</div>
	</div>
	<div style="color:lightgrey; text-align:right;">
		<p>Copyright © 2023</p>
	</div>
</footer>
<style>
	footer {
		display: flex;
		flex-direction: column;
		background:#123B4F;
		color: white;
		padding: 20px;
		font-weight: 500;
		min-height: 190px;
	}
	.main-row {
		display: flex;
		flex-direction: row;
		justify-content: space-around;
	}
	footer a {
		color: white;
		text-decoration: none;
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
