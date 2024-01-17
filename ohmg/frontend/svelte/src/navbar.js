import Navbar from '@components/shared/Navbar.svelte';

const navbar = new Navbar({
	target: document.getElementById("navbar-target"),
	props: JSON.parse(document.getElementById("navbar-props").textContent),
});

export default navbar;