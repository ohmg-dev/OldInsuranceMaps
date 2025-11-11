import './css/interface.css';
import ContributorList from './components/lists/ContributorList.svelte';
import './css/ol-overrides.css';

export default new ContributorList({
  target: document.getElementById('contributorlist-target'),
  props: JSON.parse(document.getElementById('contributorlist-props').textContent),
});
