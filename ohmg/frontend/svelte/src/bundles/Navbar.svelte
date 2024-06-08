<script>
	import IconContext from 'phosphor-svelte/lib/IconContext';
	import CaretDown from "phosphor-svelte/lib/CaretDown";
	import { iconProps } from "@lib/utils"

	import OpenModalButton from '@components/base/OpenModalButton.svelte';
    import NavbarLink from '../components/layout/NavbarLink.svelte';

	export let CONTEXT;

	const leftMenu = [
		{
			title: "Search",
			href: "/search",
		},
		{
			title: "Georeferencing",
			hasDropdown: true,
			links: [
				{
					title: "Latest Activity",
					href: "/activity",
				},
				{
					title: "Contributors",
					href: "/profiles",
				},
				{
					title: "Guides",
					href: "https://about.oldinsurancemaps.net/guides",
					isExternal: true,
				},
				{
					title: "Find a map...",
					href: "/search#items",
				},
			]
		},
		{
			title: "Community",
			hasDropdown: true,
			links: [
				{
					title: "Forum",
					href: "https://forum.openhistoricalmap.org/c/oldinsurancemaps/13",
					isExternal: true,
				},
				{
					title: "News & Newsletter",
					href: "/news",
				},
				{
					title: "FAQ",
					href: "https://about.oldinsurancemaps.net/faq",
					isExternal: true,
				},
				{
					title: "Get in touch!",
					href: "https://about.oldinsurancemaps.net/community",
					isExternal: true,
				},
			]
		},
		{
			title: "Learn more",
			hasDropdown: true,
			links: [
				{
					title: "FAQ",
					href: "https://about.oldinsurancemaps.net/faq",
					isExternal: true,
				},
				{
					title: "Contact",
					href: "https://about.oldinsurancemaps.net/contact",
					isExternal: true,
				},
				{
					title: "Sanborn Maps",
					href: "https://about.oldinsurancemaps.net/sanborn-maps",
					isExternal: true,
				},
				{
					title: "Background",
					href: "https://about.oldinsurancemaps.net",
					isExternal: true,
				},
				{
					title: "Credits",
					href: "https://about.oldinsurancemaps.net/credits",
					isExternal: true,
				},
			]
		}
	]

	function toggleBurger() {document.getElementsByClassName('navbar-burger')[0].classList.toggle('is-active')}
	function toggleMenu() {document.getElementsByClassName('navbar-menu')[0].classList.toggle('is-active')}
</script>

<IconContext values={iconProps}>
<nav class="navbar" aria-label="main navigation">
	<div class="navbar-brand">
		<a class="navbar-item" href="/">
		<img style="height:30px; width:30px;" src="/static/img/colored-full-linework.png" alt="OldInsuranceMaps.net Home">
		</a>

		<button class="navbar-burger" on:click={() => {toggleBurger(); toggleMenu()}} aria-label="menu" aria-expanded="false" data-target="navbarBasicExample">
		<span aria-hidden="true"></span>
		<span aria-hidden="true"></span>
		<span aria-hidden="true"></span>
		<span aria-hidden="true"></span>
		</button>
	</div>

	<div id="navbarBasicExample" class="navbar-menu">
		<div class="navbar-start">
		{#each leftMenu as item}
			{#if item.hasDropdown}
			<div class="navbar-item has-dropdown is-hoverable" style="border-top:none;">
				<!-- svelte-ignore a11y-missing-attribute -->
				<a class="navbar-link is-hoverable is-arrowless">
					{item.title}
					<CaretDown />
				</a>
				<div class="navbar-dropdown">
					{#each item.links as link}
					<NavbarLink title={link.title} href={link.href} isExternal={link.isExternal} />			
					{/each}
				</div>
			</div>
			{:else}
			<NavbarLink title={item.title} href={item.href} isExternal={item.isExternal} />
			{/if}
		{/each}
		</div>
		<div class="navbar-end">
		{#if CONTEXT.user.is_authenticated }
		<div class="navbar-item is-right has-dropdown is-hoverable" style="border-top:none;">
			<!-- svelte-ignore a11y-missing-attribute -->
			<a class="navbar-link is-arrowless">
				<span style="margin-right:5px">{CONTEXT.user.username}</span>
				<img style="border-radius:5px" height=32 width=32 src={CONTEXT.user.image_url} />
				<CaretDown />
			</a>
			<div class="navbar-dropdown">
				<NavbarLink title="My Profile" href={CONTEXT.user.profile_url}/>
				<NavbarLink title="Sign out" href={"/account/logout"}/>
			</div>
		</div>
		{:else}
		<div class="navbar-item is-right">
			<OpenModalButton modalId="signin-modal" style="nav-link" icon="none">Sign in</OpenModalButton>
		</div>
		{/if}
		</div>
	</div>
</nav>
</IconContext>
