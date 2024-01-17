<script>
  import TitleBar from '@components/shared/TitleBar.svelte';
  import Georeferencer from '@components/interfaces/Georeferencer.svelte';

  export let USER;
  export let SESSION_LENGTH;
  export let DOCUMENT;
  export let VOLUME;
  export let CSRFTOKEN;
  export let MAPBOX_API_KEY;

  export let TITILER_HOST;

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

<TitleBar TITLE={DOCUMENT.title} SIDE_LINKS={[]} ICON_LINKS={iconLinks}/>
<Georeferencer
  USER={USER}
  SESSION_LENGTH={SESSION_LENGTH}
  DOCUMENT={DOCUMENT}
  VOLUME={VOLUME}
  CSRFTOKEN={CSRFTOKEN}
  MAPBOX_API_KEY={MAPBOX_API_KEY}
  TITILER_HOST={TITILER_HOST}/>
