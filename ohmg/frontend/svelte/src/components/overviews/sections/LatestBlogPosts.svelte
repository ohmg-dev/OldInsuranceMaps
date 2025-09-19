<script>
  import Link from '../../common/Link.svelte';

  $: blogItems = [];

  fetch('https://blog.oldinsurancemaps.net/rss.xml')
    .then((response) => response.text())
    .then((str) => new window.DOMParser().parseFromString(str, 'text/xml'))
    .then((data) => {
      const items = data.querySelectorAll('item');
      items.forEach((el) => {
        blogItems = [
          ...blogItems,
          {
            title: el.querySelector('title').innerHTML,
            link: el.querySelector('link').innerHTML,
            pubDate: el.querySelector('pubDate').innerHTML,
            date: new Date(el.querySelector('pubDate').innerHTML).toDateString(),
          },
        ];
      });
      blogItems.sort(function (a, b) {
        return new Date(b.pubDate) - new Date(a.pubDate);
      });
      blogItems = blogItems.slice(0, 5);
    });
</script>

<div style="">
  <div class="level is-mobile" style="margin-bottom:0;">
    <div class="level-left">
      <div class="level-item">
        <h3>From the blog...</h3>
      </div>
    </div>
    <div class="level-right">
      <div class="level-item">
        <Link href="https://blog.oldinsurancemaps.net" external={true}>visit blog</Link>
      </div>
    </div>
  </div>
  <ul>
    {#each blogItems as item}
      <li style="margin-bottom: 5px;">
        <p style="margin-bottom:3px;"><Link href={item.link} external={true}>{item.title}</Link></p>
        <small>{item.date}</small>
      </li>
    {/each}
  </ul>
</div>
