<script>
import { slide } from 'svelte/transition';

let showBackground = false;
let showGuide = false;
let showVideo = false;
let showTips = false;

function setPanel(show) {

  if (show == "background") {
    showBackground = !showBackground;
    showGuide = false;
    showTips = false;
    showVideo = false;
  } else if (show == "guide") {
    showBackground = false;
    showGuide = !showGuide;
    showTips = false;
    showVideo = false;
  } else if (show == "tips") {
    showBackground = false;
    showGuide = false;
    showTips = !showTips;
    showVideo = false;
  } else if (show == "video") {
    showBackground = false;
    showGuide = false;
    showTips = false;
    showVideo = !showVideo;
  } else if (show == "none") {
    showBackground = false;
    showGuide = false;
    showTips = false;
    showVideo = false;
  }
}

</script>

<main>
  <h4>Create 3 or more ground control points to georeference this document.</h4>
  <h4>
      <a href="#" on:click={() => setPanel("background")}>Background &darr;</a>
      <a href="#" on:click={() => setPanel("guide")}>Guide &darr;</a>
      <a href="#" on:click={() => setPanel("tips")}>Tips &darr;</a>
      <a href="#" on:click={() => setPanel("video")}>Video &darr;</a>
      {#if showGuide || showVideo || showTips || showBackground}
        &nbsp;
        <a href="#" on:click={() => setPanel("none")}><i class="fa fa-close"></i></a>
      {/if}
  </h4>
  {#if showBackground}
  <div transition:slide class="help-panel">
    <h4><strong>Background</strong></h4>
    <p>
    Use this interface to create the <strong>ground control points</strong> that will be used to georeference this document. creating a ground control point requires two clicks&mdash;once in the left panel and once in the right. This records a linkage between a spot on the original map document and the real-world latitude/longitude coordinates for that location.
    </p>
    <figure style="margin-bottom:10px; text-align:center;">
        <img style="width:100%" src="/static/img/alex-3-georeference.jpg" />
        <figcaption style="">Once 3 control points are present, a semi-transparent preview will appear.</figcaption>
    </figure>
    <p>
    In the example image above, 3 control points have been made using street intersections. You can make as many control points as you want (the more the better!) but often 3-6 are enough. If 3 or more are present, a semi-transparent live preview will be added to the right panel. Use the <code>w</code> key to toggle preview transparency.
    </p>
  </div>
  {/if}
  {#if showGuide}
  <div transition:slide class="help-panel">
    <h4><strong>Using the Interface</strong></h4>
    <p>Creating a control point:</p>
    <ul>
        <li>Start a control point by clicking on the map document (left).</li>
        <li>Finish it by clicking on corresponding location in the web map (right).</li>
        <li>You can pan and zoom in both panels during this process.</li>
        <li>You can add a note to a control point. This is helpful if you are not 100% confident in your placement, or just want to point something out to future users.</li>
        <li>You can modify a control point at any time by clicking and dragging it.</li>
    </ul>
    <p>Deleting a control point:</p>
    <ul>
      <li>Select an existing control point via the list in the bottom left, or by clicking on it in the panels.</li>
      <li>Click <i class="fa fa-trash"></i> or type <code>d</code> to delete.</li>
    </ul>
    <p>Saving Control Points:</p>
    <ul>
      <li>You can only save the control points once you have 3 or more.</li>
      <li>Click <code>Save Control Points</code> when you are satisfied. This will start the warping process, which may take a few minutes to complete. You will be redirected back to the Document detail page in the meantime.</li>
      <li>Click <i class="fa fa-refresh"></i> to reset the interface. This will remove all changes you have made.</li>
    </ul>
    <p>Editing existing control points:</p>
    <ul>
        <li>If someone else has already georeferenced this document, feel free to modify their control points (or add more), to improve the georeferencing&mdash;this is meant to be an iterative process.</li>
        <li>Click <i class="fa fa-refresh"></i> to discard your changes and restore the original control points.</li>
    </ul>
    <p>Managing layers:</p>
    <ul>
      <li>You can change the opacity of the preview layer by typing <code>w</code>.</li>
      <li>You can switch to an aerial imagery basemap with the <code>Basemap</code> dropdown menu.</li>
    </ul>
    <p>Managing the panels:</p>
    <ul>
      <li>You can increase the size of the left or right panel with the menu in the top left.</li>
      <li>Checking the <code>autosize</code> box will cause the panels sizes to dynamically update based on whether your next click should be in the left or right panel.</li>
    </ul>
    <p>Transformations:</p>
    <ul>
      <li>It is recommended that you use the default transformation, <code>Polynomial</code>.</li>
      <li>Switching to <code>Thin Plate Spline</code> will allow the image to distort and warp to fit all control points exactly, which <em>could</em> be necessary in rare circumstances.</li>
      <li>You can read more about GDAL transformation algorithms in the <a href="https://docs.qgis.org/3.16/en/docs/user_manual/working_with_raster/georeferencer.html#available-transformation-algorithms" target="_blank">QGIS documentation <i class="fa fa-external-link"></i></a> (note: we are only using the Polynomial 1 transformation here).</li>
    </ul>
  </div>
  {/if}
  {#if showTips}
  <div transition:slide class="help-panel">
    <h4><strong>Tips</strong></h4>
    <ul>
      <li>Before starting, pan and zoom around to become familiar with the document and the area.</li>
      <li>Prioritize finding control points that are widely spread across the map.</li>
      <li>Look for locations that have changed the least over time:
        <ul>
          <li>the center of street intersections</li>
          <li>railroad crossings</li>
          <li>or, in some cases, the corners or centers of old buildings</li>
        </ul>
      </li>
      <li>Avoid using are the edges of city blocks, sidewalks, or street intersections where you can't see all four corners.</li>
      <li>Historical maps may have mistakes, or street names may have changed over time.</li>
      <li>If you are unsure about a control point, add a note to it for future reference.</li>
    </ul>
  </div>
  {/if}
  {#if showVideo}
  <div transition:slide class="help-panel">
    <h4><em>coming soon!</em></h4>
  </div>
  {/if}
</main>

<style>

main {
  display: flex;
  flex-direction: column;
}

figcaption {
  font-style: italic;
  font-size: .85em;
}

.help-panel {
  font-size: 1.25em;
  background: lightgray;
  border-radius: 7px;
  padding: 20px;
  margin-top: 20px;
  margin-bottom: 20px;
}

</style>
