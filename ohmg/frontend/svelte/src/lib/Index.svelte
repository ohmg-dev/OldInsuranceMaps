<script>
    import IconContext from 'phosphor-svelte/lib/IconContext';
    import '../css/shared.css'
    import Browse from './Browse.svelte'
    import Home from './Home.svelte'
    import About from './About.svelte'
    import FAQ from './FAQ.svelte'
    import Contact from './Contact.svelte'
    import Profile from './Profile.svelte'
    import Participants from './Participants.svelte'
    import Place from './Place.svelte'
    import GettingStarted from './GettingStarted.svelte'
    import Activity from './Activity.svelte'
    import FireInsuranceMaps from './FireInsuranceMaps.svelte';

    export let PAGE_NAME = '';
    export let PARAMS = {};

</script>

<IconContext values={{ weight:'bold'}} >
{#if PAGE_NAME == 'home'}
<Home 
    ITEM_API_URL={PARAMS.ITEM_API_URL}
    SESSION_API_URL={PARAMS.SESSION_API_URL}
    PLACES_GEOJSON_URL={PARAMS.PLACES_GEOJSON_URL}
    IS_MOBILE={PARAMS.IS_MOBILE}
    CSRFTOKEN={PARAMS.CSRFTOKEN}
    OHMG_API_KEY={PARAMS.OHMG_API_KEY}
    NEWSLETTER_SLUG={PARAMS.NEWSLETTER_SLUG}
    USER_SUBSCRIBED={PARAMS.USER_SUBSCRIBED}
    USER_EMAIL={PARAMS.USER_EMAIL}
    VIEWER_SHOWCASE={PARAMS.VIEWER_SHOWCASE}
    PLACES_CT={PARAMS.PLACES_CT}
    ITEMS_CT={PARAMS.ITEMS_CT} />
{:else if PAGE_NAME == 'about'}
<About />
{:else if PAGE_NAME == 'about-sanborn-maps'}
<FireInsuranceMaps />
{:else if PAGE_NAME == 'faq'}
<FAQ />
{:else if PAGE_NAME == 'contact'}
<Contact />
{:else if PAGE_NAME == 'getting-started'}
<GettingStarted />
{:else if PAGE_NAME == 'profile'}
<Profile 
    CURRENT_USERNAME={PARAMS.CURRENT_USERNAME}
    PROFILE_USER={PARAMS.PROFILE_USER}
    CHANGE_AVATAR_URL={PARAMS.CHANGE_AVATAR_URL}
    SESSION_API_URL={PARAMS.SESSION_API_URL}
    OHMG_API_KEY={PARAMS.OHMG_API_KEY}
    USER_API_KEYS={PARAMS.USER_API_KEYS} />
{:else if PAGE_NAME == 'activity'}
<Activity 
    SESSION_API_URL={PARAMS.SESSION_API_URL}
    OHMG_API_KEY={PARAMS.OHMG_API_KEY} />
{:else if PAGE_NAME == 'profiles'}
<Participants
    USER_API_URL={PARAMS.USER_API_URL}
    OHMG_API_KEY={PARAMS.OHMG_API_KEY} />
{:else if PAGE_NAME == 'place'}
<Place 
    PLACE={PARAMS.PLACE} />
{:else if PAGE_NAME == 'browse'}
<Browse 
    PLACES_GEOJSON_URL={PARAMS.PLACES_GEOJSON_URL}
    PLACES_CT={PARAMS.PLACES_CT}
    PLACES_API_URL={PARAMS.PLACES_API_URL}
    ITEM_CT={PARAMS.ITEM_CT}
    ITEM_API_URL={PARAMS.ITEM_API_URL}
    OHMG_API_KEY={PARAMS.OHMG_API_KEY} />
{/if}
</IconContext>
