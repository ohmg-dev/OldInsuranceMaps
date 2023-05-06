import '../css/shared.css';
import Profile from '../components/Profile.svelte';

const profile = new Profile({
	target: document.getElementById("profile-target"),
	props: JSON.parse(document.getElementById("profile-props").textContent),
});

export default profile;