<script>
    import '@src/css/shared.css'
    import Browse from '@components/overviews/Browse.svelte'
    import Home from '@components/Home.svelte'
    import Place from '@components/overviews/Place.svelte'
    import Profile from '@components/overviews/Profile.svelte'
    import Participants from '@components/lists/Participants.svelte'
    import SessionList from '@components/lists/SessionList.svelte'

    import TitleBar from '@components/layout/TitleBar.svelte';
    import MarkdownPage from '@components/layout/MarkdownPage.svelte';

    export let PAGE_NAME = '';
    export let PARAMS = {};
    export let CONTEXT = {};

</script>

{#if PAGE_NAME == 'home'}
<Home 
    {CONTEXT}
    NEWSLETTER_SLUG={PARAMS.NEWSLETTER_SLUG}
    USER_SUBSCRIBED={PARAMS.USER_SUBSCRIBED}
    PLACES_CT={PARAMS.PLACES_CT}
    MAP_CT={PARAMS.MAP_CT} />
{:else if PAGE_NAME == 'profile'}
<TitleBar TITLE={PARAMS.PROFILE_USER.username} IMG_URL={PARAMS.PROFILE_USER.image_url} />
<Profile
    {CONTEXT}
    PROFILE_USER={PARAMS.PROFILE_USER} />
{:else if PAGE_NAME == 'activity'}
<TitleBar TITLE={"All activity"} />
<SessionList
    {CONTEXT}
    limit={"25"} showThumbs={true}/>
{:else if PAGE_NAME == 'profiles'}
<TitleBar TITLE={"Participants"} />
<Participants
    {CONTEXT} />
{:else if PAGE_NAME == 'place'}
<Place
    {CONTEXT}
    PLACE={PARAMS.PLACE} />
{:else if PAGE_NAME == 'browse'}
<Browse 
    {CONTEXT}
    PLACES_CT={PARAMS.PLACES_CT}
    MAP_CT={PARAMS.MAP_CT} />
{:else if PAGE_NAME == 'markdown-page'}
<MarkdownPage 
    HEADER={PARAMS.HEADER}
    source={PARAMS.source} />
{/if}
