<script>
import IconContext from 'phosphor-svelte/lib/IconContext';
import { iconProps } from "../js/utils"
import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";
import CaretDown from "phosphor-svelte/lib/CaretDown";

export let USER;
let showAboutDD = false;
let showContribDD = false;

function clickOutside(node, { enabled: initialEnabled, cb }) {
    const handleOutsideClick = ({ target }) => {
      if (!node.contains(target)) {
        cb();
      }
    };

    function update({enabled}) {
      if (enabled) {
        window.addEventListener('click', handleOutsideClick);
      } else {
        window.removeEventListener('click', handleOutsideClick);
      }
    }

    update({ enabled: initialEnabled });
    return {
      update,
      destroy() {
        window.removeEventListener( 'click', handleOutsideClick );
      }
    };
  }
</script>

<IconContext values={iconProps}>
<nav class="lahmg-nav ">
	<div>
		<div>
			<a href="/" title="LaHMG">
				<img style="height:45px; width:45px;" src="/static/img/colored-full-linework.png" alt="LaHMG" class="navbar-brand-new">
			</a>
		</div>
		<div style="padding-left: 8px;">
			<a href="/browse">Search</a>
		</div>
		<div class="dropdown-container {showContribDD ? 'active' : ''}" use:clickOutside={{ enabled: showContribDD, cb: () => showContribDD = false }} >
			<button on:click={() => {showContribDD = !showContribDD}} title="Georeferencing">Georeferencing <CaretDown /></button>
			{#if showContribDD}
			<div class="dropdown">
				<a href="/browse#items" title="Find an item to work on">Find an item...</a>
				<!-- <a href="/getting-started" title="Getting started">Getting started</a> -->
				<a href="/profiles" title="All contributors">All contributors</a>
				<a href="/activity" title="All activity">All activity</a>
				<a href="https://ohmg.dev/docs" title="Full documentation on ohmg.dev" target="_blank">Full documentation <ArrowSquareOut /></a>
			</div>
			{/if}
		</div>
		<div class="dropdown-container {showAboutDD ? 'active' : ''}" use:clickOutside={{ enabled: showAboutDD, cb: () => showAboutDD = false }} >
			<button on:click={() => {showAboutDD = !showAboutDD}} title="About">About <CaretDown /></button>
			{#if showAboutDD}
			<div class="dropdown">
				<a href="/faq" title="Frequently Asked Questions">FAQ</a>
				<a href="/newsletter/lahmg-news/" title="Newsletter">Newsletter</a>
				<a href="/contact" title="Contact">Contact</a>
				<a href="/about-sanborn-maps" title="About Sanborn maps">About Sanborn maps</a>
				<a href="/about" title="About this site...">About this site...</a>
			</div>
			{/if}
		</div>
	</div>
	<div>
		<div>
			{#if USER.is_authenticated }
			<a href={USER.profile}>{USER.name}</a>
			{:else}
			<a href="/account/login">Sign in</a>
			{/if}
		</div>
	</div>
</nav>
</IconContext>
<style>
nav.lahmg-nav {
	display: flex;
	height: 60px;
	background:#123B4F;
	box-shadow: rgba(0, 0, 0, 0.1) 0px 1px 2px 0px;
    position: fixed;
    top: 0;
    right: 0;
    left: 0;
    z-index: 1030;
    display: flex;
    align-items: center;
    justify-content: space-between;
	padding: 0px 10px;
	color:white;
	font-weight: 500;
	overflow-x: auto;
	border: none;
	max-width: 100vw;
}

nav.lahmg-nav a {
	color:white;
}

nav.lahmg-nav a:hover {
	color: #cecece;
	text-decoration: none;
}

nav.lahmg-nav button:hover {
	color: #cecece;
}

nav.lahmg-nav > div {
	display: flex;
	align-items: center;
}

nav.lahmg-nav > div > div {
	padding: 4px;
	white-space: nowrap;
}

.dropdown {
	display:flex;
	flex-direction: column;
	align-items: baseline;
	position:fixed;
	top:50px;
	background: #123B4F;
	padding: 10px 15px;
}
.dropdown a {
	margin: 2px 0px;
}

.active {
	color: #cecece;
}

.dropdown-container button {
	display: flex;
	flex-direction: row;
	align-items: center;
	background: none;
	border: none;
}

@media (max-width: 760px) {
	.dropdown {
		right: 0;
	}
	nav.lahmg-nav {
		padding: 0px 5px;
	}
}

</style>
