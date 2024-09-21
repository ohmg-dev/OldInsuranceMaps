<script>
  import TitleBar from '@components/layout/TitleBar.svelte';
  import Splitter from '@components/interfaces/Splitter.svelte';

  export let CONTEXT;
  export let DOCUMENT;

  const iconLinks = [
    {
      visible: true,
      enabled: true,
      iconClass: 'document',
      alt: 'Go to document: ' + DOCUMENT.title,
      url: DOCUMENT.urls.resource,
    },
    {
      visible: true,
      enabled: false,
      iconClass: 'layer',
      alt: '',
      url: '',
    },
    {
      visible: true,
      enabled: true,
      iconClass: 'volume',
      alt: 'Back to map overview',
      url: `/map/${DOCUMENT.map}`,
    }
  ]
</script>

<TitleBar TITLE={DOCUMENT.title} ICON_LINKS={iconLinks}/>
<Splitter {CONTEXT} {DOCUMENT} />
