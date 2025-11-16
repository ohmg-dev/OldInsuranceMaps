<script>
  import Link from '../common/Link.svelte';

  export let MAP;
</script>

<article class="media" style="flex-direction:row; align-items:center;">
  <figure class="media-left">
    <img src={MAP.thumbnail_url} style="height:50px;" alt="thumb" />
  </figure>
  <div class="">
    <div class="">
      <strong><Link href={MAP.urls.summary} title="{MAP.title} summary">{MAP.title}</Link></strong>
      <small style="color:#6f6f6f">{MAP.sheet_ct == 1 ? 'single page' : `${MAP.sheet_ct} pages`}</small>
      <br />
      <em>Loaded by <Link href={MAP.loaded_by.profile_url}>{MAP.loaded_by.username}</Link>, {MAP.load_date}</em>
    </div>
    <nav class="level is-mobile">
      <div class="level-left">
        <small></small>
      </div>
    </nav>
  </div>
</article>
