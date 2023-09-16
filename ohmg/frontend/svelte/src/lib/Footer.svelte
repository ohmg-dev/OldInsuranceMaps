<script>
	import IconContext from 'phosphor-svelte/lib/IconContext';
	import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";
	import { iconProps } from "../js/utils"
</script>

<IconContext values={iconProps} >
<footer class="lahmg-footer">
	<div class="main-row">
		<div>
			<h4>Content</h4>
			<ul>
				<li><a href="/browse">Search Maps</a></li>
				<li><a href="/profiles">Contributors</a></li>
				<li><a href="https://github.com/mradamcox/ohmg">GitHub <ArrowSquareOut /></a></li>
			</ul>
		</div>
		<div>
			<h4>Learn More</h4>
			<ul>
				<li><a href="/faq">FAQ</a></li>
				<li><a href="/about-sanborn-maps">About Sanborn Maps</a></li>
				<li><a href="https://ohmg.dev/docs">Documentation <ArrowSquareOut /></a></li>
			</ul>
		</div>
		<div>
			<h4>News & Updates</h4>
			<ul>
				<li><a href="/newsletter/lahmg-news/archive" >Newsletter Archive</a></li>
				<li><a href="/contact" >Contact</a></li>
				<li><a href="https://ohmg.dev/blog" >Blog <ArrowSquareOut /></a></li>
			</ul>
		</div>
	</div>
	<div style="color:lightgrey; text-align:right;">
		<p>Copyright © 2023</p>
	</div>
</footer>
</IconContext>
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
