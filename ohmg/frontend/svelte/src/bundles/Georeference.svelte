<script>
  import TitleBar from '@components/layout/TitleBar.svelte';
  import Georeferencer from '@components/interfaces/Georeferencer.svelte';

  export let CONTEXT;
  export let DOCUMENT;
  export let VOLUME;
  export let ANNOSET_MAIN;
  export let ANNOSET_KEYMAP;

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
      enabled: DOCUMENT.layer ? true : false,
      iconClass: 'layer',
      alt: DOCUMENT.layer ? 'Go to layer: ' + DOCUMENT.layer.title : 'Layer not yet made',
      url: DOCUMENT.layer ? DOCUMENT.layer.urls.resource : '',
    },
    {
      visible: true,
      enabled: true,
      iconClass: 'volume',
      alt: 'Go to volume: ' + VOLUME.title,
      url: VOLUME.urls.summary,
    }
  ]

</script>

<TitleBar TITLE={DOCUMENT.title} ICON_LINKS={iconLinks}/>
<Georeferencer {CONTEXT} {DOCUMENT} {VOLUME} {ANNOSET_MAIN} {ANNOSET_KEYMAP} />
