<script>
    import IconContext from 'phosphor-svelte/lib/IconContext';
    import '@src/css/shared.css'
    import Browse from './Browse.svelte'
    import Home from './Home.svelte'
    import Profile from '@components/overviews/Profile.svelte'
    import Participants from '@components/lists/Participants.svelte'
    import Place from './Place.svelte'
    import SessionList from '@components/lists/SessionList.svelte'

    import TitleBar from '../components/layout/TitleBar.svelte';
    import MarkdownPage from '../components/layout/MarkdownPage.svelte';

    export let PAGE_NAME = '';
    export let PARAMS = {};

</script>

<IconContext values={{ weight:'bold'}} >
{#if PAGE_NAME == 'home'}
<Home 
    ROUTES={PARAMS.ROUTES}
    IS_MOBILE={PARAMS.IS_MOBILE}
    CSRFTOKEN={PARAMS.CSRFTOKEN}
    NEWSLETTER_SLUG={PARAMS.NEWSLETTER_SLUG}
    USER_SUBSCRIBED={PARAMS.USER_SUBSCRIBED}
    USER_EMAIL={PARAMS.USER_EMAIL}
    VIEWER_SHOWCASE={PARAMS.VIEWER_SHOWCASE}
    PLACES_CT={PARAMS.PLACES_CT}
    MAP_CT={PARAMS.MAP_CT} />
{:else if PAGE_NAME == 'profile'}
<TitleBar TITLE={PARAMS.PROFILE_USER.username} IMG_URL={PARAMS.PROFILE_USER.image_url} />
<Profile 
    ROUTES={PARAMS.ROUTES}
    CURRENT_USERNAME={PARAMS.CURRENT_USERNAME}
    PROFILE_USER={PARAMS.PROFILE_USER}
    USER_API_KEYS={PARAMS.USER_API_KEYS} />
{:else if PAGE_NAME == 'activity'}
<TitleBar TITLE={"All activity"} />
<SessionList
    ROUTES={PARAMS.ROUTES}
    limit={"25"} showThumbs={true}/>
{:else if PAGE_NAME == 'profiles'}
<TitleBar TITLE={"Participants"} />
<Participants
    ROUTES={PARAMS.ROUTES} />
{:else if PAGE_NAME == 'place'}
<Place 
    PLACE={PARAMS.PLACE}
    ROUTES={PARAMS.ROUTES} />
{:else if PAGE_NAME == 'browse'}
<Browse 
    ROUTES={PARAMS.ROUTES}
    PLACES_CT={PARAMS.PLACES_CT}
    MAP_CT={PARAMS.MAP_CT} />
{:else if PAGE_NAME == 'markdown-page'}
<MarkdownPage 
    HEADER={PARAMS.HEADER}
    source={PARAMS.source} />
{/if}
</IconContext>
