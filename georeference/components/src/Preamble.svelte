<script>
import { slide } from 'svelte/transition';

export let DOCUMENT;


</script>

<main>
  {DOCUMENT.title}
</main>

<style>

main {
  display: flex;
  flex-direction: column;
}

i {
  width: 20px;
  text-align: center;
}

button:enabled {
  color: white;
  background-color: #2c689c;
  border-radius: 4px;
  border: 1px solid transparent;
}

button:hover:enabled {
  color: white;
  background-color: #204d74;
  border-color: #193b58;
}

.btn-chosen {
  border: 2px solid #2c2c2c;
  border-radius: 4px;
}

section {
  border-bottom: 1px dashed #ddd;
}

section h4 i {
  font-size: .65em;
}
section h4 {
  color: #2c689c;
  cursor: pointer;
}

.section-body {
  margin: 10px 0px;
}

table {
	min-width:100%;
  border: 1px solid #ddd;
}

table caption {
  color: #333;
  text-align: center;
}

th, td {
	padding: 4px;
}

th {
  font-variant: small-caps;
  font-size: .85em;
}

tr:nth-child(even) {
  background-color: #f6f6f6;
}

tr:nth-child(odd) {
  background-color: #ffffff;
}

.coord-digit {
  font-family: Menlo, monospace;
  font-size: .85em;
}

.documents-column {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 20px;
}

.document-item {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid gray;
  background: white;

}

.document-item img {
  margin: 15px;
  max-height: 200px;
  max-width: 200px;
}

.document-item div:first-child {
  text-align: center;
}

.document-item div:first-child, .document-item div:last-child {
  padding: 10px;
  background: #e6e6e6;
  width: 100%;
}

.document-item p, .document-item ul {
  margin: 0px;
}

.document-item ul {
  list-style-type: none;
  padding: 0;
}

#refresh-button {
  float: right;
}

</style>
