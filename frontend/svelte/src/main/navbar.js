// import '../css/shared.css';
import Navbar from './Navbar.svelte';
// import Header from '../components/Header.svelte';

const navbar = new Navbar({
	target: document.getElementById("navbar-target"),
	props: JSON.parse(document.getElementById("navbar-props").textContent),
});

export default navbar;