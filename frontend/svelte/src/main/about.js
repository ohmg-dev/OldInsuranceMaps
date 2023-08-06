import About from './About.svelte';

const about = new About({
	target: document.getElementById("about-target"),
	props: JSON.parse(document.getElementById("about-props").textContent),
});

export default about;