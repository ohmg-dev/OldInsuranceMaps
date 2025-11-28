import ContributorList from './components/lists/ContributorList.svelte';

export default new ContributorList({
  target: document.getElementById('contributorlist-target'),
  props: JSON.parse(document.getElementById('contributorlist-props').textContent),
});
