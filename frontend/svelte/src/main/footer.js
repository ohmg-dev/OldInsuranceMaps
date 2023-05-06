import '../css/shared.css';
import Footer from '../components/Footer.svelte';

const footer = new Footer({
	target: document.getElementById("footer-target"),
	props: JSON.parse(document.getElementById("footer-props").textContent),
});

export default footer;