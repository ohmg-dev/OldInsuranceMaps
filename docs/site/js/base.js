"use strict";

// The full page consists of a main window with navigation and table of contents, and an inner
// iframe containing the current article. Which article is shown is determined by the main
// window's #hash portion of the URL. In fact, we use the simple rule: main window's URL of
// "rootUrl#relPath" corresponds to iframe's URL of "rootUrl/relPath".

var outerWindow = is_outer_page ? window : (window === window.parent ? null : window.parent);
var innerWindow = null;
var rootUrl = qualifyUrl(base_url);
var searchIndex = null;
var showPageToc = true;
var MutationObserver = window.MutationObserver || window.WebKitMutationObserver;

var Keys = {
	ENTER:  13,
	ESCAPE: 27,
	UP:     38,
	DOWN:   40,
};

if (is_outer_page) {
	// Main window.
	$(document).ready(function() {
		innerWindow = $('.wm-article')[0].contentWindow;
		initMainWindow();
		ensureIframeLoaded();
	});

} else {
	// Article contents.
	innerWindow = window;
	if (outerWindow) {
		outerWindow.onIframeLoad();
	} else {
		// This is a page that ought to be in an iframe. Redirect to load the top page instead.
		var topUrl = getAbsUrl('#', getRelPath('/', window.location.href));
		if (topUrl) {
			window.location.href = topUrl;
		}
	}

	// Other initialization of iframe contents.
	hljs.initHighlightingOnLoad();
	$(document).ready(function() {
		$('table').addClass('table table-striped table-hover table-bordered table-condensed');
		$('a').filter(function(i, val) {
			val = $(val);
			return val.attr("href") && val.attr("href").match(/^\w+:\/\//);
		}).attr("target", "_blank");
	});
}

function startsWith(str, prefix) { return str.lastIndexOf(prefix, 0) === 0; }
function endsWith(str, suffix) { return str.indexOf(suffix, str.length - suffix.length) !== -1; }

/**
 * Creates event handlers for click and the enter key
 */
function onActivate(sel, arg1, arg2) {
	if (arg2 === undefined) {
		$(sel).on('click', function(){ arg1($(this)); });
		$(sel).on('keydown', function(e){ if(e.which === 13 || e.which === 32) arg1($(this)); });
	} else {
		$(sel).on('click', arg1, function(){ arg2($(this)); });
		$(sel).on('keydown', arg1, function(e){ if(e.which === 13 || e.which === 32) arg2($(this)); });
	}
}

/**
 * Returns whether to use small-screen mode. Note that the same size is used in css @media block.
 */
function isSmallScreen() {
	return window.matchMedia("(max-width: 767.98px)").matches;
}

/**
 * Given a relative URL, returns the absolute one, relying on the browser to convert it.
 */
function qualifyUrl(url) {
	var a = document.createElement('a');
	a.href = url;
	return a.href;
}

/**
 * Turns an absolute path to relative, stripping out rootUrl + separator.
 */
function getRelPath(separator, absUrl) {
	var prefix = rootUrl + (endsWith(rootUrl, separator) ? '' : separator);
	return startsWith(absUrl, prefix) ? absUrl.slice(prefix.length) : null;
}

/**
 * Turns a relative path to absolute, adding a prefix of rootUrl + separator.
 */
function getAbsUrl(separator, relPath) {
	var sep = endsWith(rootUrl, separator) ? '' : separator;
	return relPath === null ? null : rootUrl + sep + relPath;
}

/**
 * Redirects the iframe to reflect the path represented by the main window's current URL.
 * (In our design, nothing should change iframe's src except via updateIframe(), or back/forward
 * history is likely to get messed up.)
 */
function updateIframe(enableForwardNav) {
	// Grey out the "forward" button if we don't expect 'forward' to work.
	$('#hist-fwd').toggleClass('greybtn', !enableForwardNav);

	var targetRelPath = (getRelPath('#', outerWindow.location.href) || "").replace("~", "#");
	var targetIframeUrl;
	if (targetRelPath.length <= 1) {
		targetIframeUrl = home_url;
	} else {
		targetIframeUrl = getAbsUrl('/', targetRelPath);
	}
	var innerLoc = innerWindow.location;
	var currentIframeUrl = _safeGetLocationHref(innerLoc);

	console.log("updateIframe: %s -> %s (%s)", currentIframeUrl, targetIframeUrl,
		currentIframeUrl === targetIframeUrl ? "same" : "replacing");

	if (currentIframeUrl !== targetIframeUrl) {
		innerLoc.replace(targetIframeUrl);
		onIframeBeforeLoad(targetIframeUrl);
	}
	document.body.scrollTop = 0;
}

/**
 * Returns location.href, catching exception that's triggered if the iframe is on a different domain.
 */
function _safeGetLocationHref(location) {
	try {
		return location.href;
	} catch (e) {
		return null;
	}
}

/**
 * Returns the value of the given parameter in the URL's query portion.
 */
function getParam(key) {
	var params = window.location.search.substring(1).split('&');
	for (var i = 0; i < params.length; i++) {
		var param = params[i].split('=');
		if (param[0] === key) {
			return decodeURIComponent(param[1].replace(/\+/g, '%20'));
		}
	}
}

/**
 * Update the height of the iframe container. On small screens, we adjust it to fit the iframe
 * contents, so that the page scrolls as a whole rather than inside the iframe.
 */
function onResize() {
	if (isSmallScreen()) {
		if ($('.wm-article').attr('scrolling') !== 'no') {
			$('#wm-search-form').removeClass('show');
			$('.wm-article').attr('scrolling', 'no');
		}
		$('.wm-toc-pane').css('top', $('.navbar').height());
		$('.wm-content-pane').height(innerWindow.document.body.offsetHeight + 20);
	} else {
		$('#wm-search-form').addClass('show');
		$('.wm-content-pane').height('');
		$('.wm-article').attr('scrolling', 'auto');
		$('.wm-toc-pane').css('top', 0);
	}
}

/**
 * Close TOC on small screens and hide the search
 */
function closeTempItems() {
	if (isSmallScreen()) {
		$('.wm-toc-triggered').removeClass('wm-toc-triggered');
	}
	$('#mkdocs-search-container').dropdown('hide');
}

/**
 * Adjusts link to point to a top page, converting URL from "base/path" to "base#path". It also
 * sets a data-adjusted attribute on the link, to skip adjustments on future clicks.
 */
function adjustLink(linkEl) {
	var relPath = getRelPath('/', linkEl.href);
	if (relPath !== null) {
		var newUrl = getAbsUrl('#', relPath.replace('#', '~'));
		linkEl.href = newUrl;
	}
}

/**
 * Given a URL, strips query and fragment, returning just the path.
 */
function cleanUrlPath(relUrl) {
	return relUrl.replace(/[#?].*/, '');
}

/**
 * Initialize the main window.
 */
function initMainWindow() {
	// wm-toc-button either opens the table of contents in the side-pane, or (on smaller screens)
	// shows the side-pane as a drop-down.
	$('#wm-toc-button').on('click', function(e) {
		if (isSmallScreen()) {
			window.scroll(0,0);
		}
		$('#main-content').toggleClass('wm-toc-triggered');
	});

	$(window).on('resize', onResize);

	// Connect up the Back and Forward buttons (if present).
	$('#hist-back').on('click', function(e) { window.history.back(); });
	$('#hist-fwd').on('click', function(e) { window.history.forward(); });

	// When the side-pane is a dropdown, hide it on click-away.
	$(window).on('blur', closeTempItems);

	// When we click on an opener in the table of contents, open it.
	onActivate('.wm-toc-pane', '.wm-toc-opener', ele => {
		ele.toggleClass('wm-toc-open');
		ele.next('.wm-toc-li-nested').collapse('toggle');
	});
	onActivate('.wm-toc-pane', '.wm-page-toc-opener', ele => {
		// Ignore clicks while transitioning.
		if (ele.next('.wm-page-toc').hasClass('collapsing')) { return; }
		showPageToc = !showPageToc;
		ele.toggleClass('wm-page-toc-open', showPageToc);
		ele.next('.wm-page-toc').collapse(showPageToc ? 'show' : 'hide');
	});
	onActivate('.wm-toc-pane', 'a', () => {
		$('.wm-toc-pane').toggleClass('wm-toc-triggered');
	});

	// Once the article loads in the side-pane, close the dropdown.
	$('.wm-article').on('load', function() {
		onInnerWindowUpdated();

		document.title = innerWindow.document.title;
		onResize();

		// We want to update content height whenever the height of the iframe's content changes.
		// Using MutationObserver seems to be the best way to do that.
		var observer = new MutationObserver(onResize);
		observer.observe(innerWindow.document.body, {
			attributes: true,
			childList: true,
			characterData: true,
			subtree: true
		});

		innerWindow.focus();
	});

	// Initialize search functionality.
	initSearch();

	// Load the iframe now, and whenever we navigate the top frame.
	setTimeout(function() { updateIframe(false); }, 0);
	// For our usage, 'popstate' or 'hashchange' would work, but only 'hashchange' works on IE.
	$(window).on('hashchange', function() { updateIframe(true); });
}

function onInnerWindowUpdated() {
	window.history.replaceState(null, '', getAbsUrl('#', getRelPath('/', innerWindow.location.href).replace('#', '~')));
	$('#mkdocs-search-results').collapse('hide');
}

function onIframeBeforeLoad(url) {
	$('.wm-current').removeClass('wm-current');
	closeTempItems();

	var tocLi = getTocLi(url);
	tocLi.addClass('wm-current');
	tocLi.parents('.wm-toc-li-nested')
	// It's better to open parent items immediately without a transition.
		.removeClass('collapsing').addClass('collapse show').height('')
		.prev('.wm-toc-opener').addClass('wm-toc-open');
}

function getTocLi(url) {
	var relPath = getRelPath('/', cleanUrlPath(url));
	var selector = '.wm-article-link[href="' + relPath + '"]';
	return $(selector).closest('.wm-toc-li');
}

var _deferIframeLoad = false;

// Sometimes iframe is loaded before main window's ready callback. In this case, we defer
// onIframeLoad call until the main window has initialized.
function ensureIframeLoaded() {
	if (_deferIframeLoad) {
		onIframeLoad();
	}
}

function onIframeLoad() {
	if (!innerWindow) { _deferIframeLoad = true; return; }
	var url = innerWindow.location.href;
	onIframeBeforeLoad(url);
	$(innerWindow).on('hashchange', onInnerWindowUpdated);

	if (innerWindow.pageToc) {
		var relPath = getAbsUrl('#', getRelPath('/', cleanUrlPath(url)));
		var li = getTocLi(url);
		if (!li.hasClass('wm-page-toc-open')) {
			renderPageToc(li, relPath, innerWindow.pageToc);
		}
	} else {
		//collapseAndRemove($('.wm-page-toc'));
	}

	innerWindow.focus();
}

/**
 * Hides a bootstrap collapsible element, and removes it from DOM once hidden.
 */
function collapseAndRemove(collapsibleElem) {
	collapsibleElem.on('hidden.bs.collapse', function() {
		collapsibleElem.remove();
	})
	.collapse('hide');
}

function renderPageToc(parentElem, pageUrl, pageToc) {
	var ul = $('<ul class="wm-page-toc-tree">');
	function addItem(tocItem) {
		ul.append($('<li class="wm-toc-li">')
			.append($('<a class="wm-article-link wm-page-toc-text">')
				.attr('href', pageUrl + tocItem.url.replace("#", "~"))
				.attr('data-cm-adjusted', 'done')
				.text(tocItem.title)));
		if (tocItem.children) {
			tocItem.children.forEach(addItem);
		}
	}
	pageToc.forEach(addItem);

	$('.wm-page-toc-opener').removeClass('wm-page-toc-opener wm-page-toc-open');
	collapseAndRemove($('.wm-page-toc'));

	parentElem.addClass('wm-page-toc-opener').toggleClass('wm-page-toc-open', showPageToc);
	$('<li class="wm-page-toc wm-toc-li-nested collapse">').append(ul).insertAfter(parentElem)
		.collapse(showPageToc ? 'show' : 'hide');
}

var searchIndexReady = false;

/**
 * Initialize search functionality.
 */
function initSearch() {
	// Create elasticlunr index.
	searchIndex = elasticlunr(function() {
		this.setRef('location');
		this.addField('title');
		this.addField('text');
	});

	var searchBox = $('#mkdocs-search-query');
	var searchResults = $('#mkdocs-search-results');

	// Fetch the prebuilt index data, and add to the index.
	$.getJSON(base_url + '/search/search_index.json')
		.done(function(data) {
			data.docs.forEach(function(doc) {
				searchIndex.addDoc(doc);
			});
			searchIndexReady = true;
			$(document).trigger('searchIndexReady');
		});

	function showSearchResults(optShow) {
		var show = (optShow === false ? false : Boolean(searchBox.val()));
		if (show) {
			doSearch({
				resultsElem: searchResults,
				query: searchBox.val(),
				snippetLen: 100,
				limit: 10
			});
		}
		searchResults.collapse(show ? 'show' : 'hide');
		return show;
	}

	searchBox.on('click', function(e) {
		if (!searchResults.hasClass('show')) {
			if (showSearchResults()) {
				e.stopPropagation();
			}
		}
	});

	// Search automatically and show results on keyup event.
	searchBox.on('keyup', function(e) {
		var show = (e.which !== Keys.ESCAPE && e.which !== Keys.ENTER);
		showSearchResults(show);
	});

	// Open the search box (and run the search) on up/down arrow keys.
	searchBox.on('keydown', function(e) {
		if (e.which === Keys.UP || e.which === Keys.DOWN) {
			if (showSearchResults()) {
				e.stopPropagation();
				e.preventDefault();
				setTimeout(function() {
					searchResults.find('a').eq(e.which === Keys.UP ? -1 : 0).focus();
				}, 0);
			}
		}
	});

	searchResults.on('keydown', function(e) {
		if (e.which === Keys.UP || e.which === Keys.DOWN) {
			if (searchResults.find('a').eq(e.which === Keys.UP ? 0 : -1)[0] === e.target) {
				searchBox.focus();
				e.stopPropagation();
				e.preventDefault();
			} else {
				if (e.which === Keys.UP) {
					$(e.target).prevAll('a')[0].focus();
				} else {
					$(e.target).nextAll('a')[0].focus();
				}
			}
		} else if (e.which !== Keys.ENTER) {
			searchBox.focus();
		}
	});
}

function escapeRegex(s) {
	return s.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
}

/**
 * This helps construct useful snippets to show in search results, and highlight matches.
 */
function SnippetBuilder(query) {
	var termsPattern = elasticlunr.tokenizer(query).map(escapeRegex).join("|");
	this._termsRegex = termsPattern ? new RegExp(termsPattern, "gi") : null;
}

SnippetBuilder.prototype.getSnippet = function(text, len) {
	if (!this._termsRegex) {
		return text.slice(0, len);
	}

	// Find a position that includes something we searched for.
	var pos = text.search(this._termsRegex);
	if (pos < 0) { pos = 0; }

	// Find a period before that position (a good starting point).
	var start = text.lastIndexOf('.', pos) + 1;
	if (pos - start > 30) {
		// If too long to previous period, give it 30 characters, and find a space before that.
		start = text.lastIndexOf(' ', pos - 30) + 1;
	}
	var rawSnippet = text.slice(start, start + len);
	return rawSnippet.replace(this._termsRegex, '<b>$&</b>');
};

/**
 * Search the elasticlunr index for the given query, and populate the dropdown with results.
 */
function doSearch(options) {
	var resultsElem = options.resultsElem;
	resultsElem.empty();

	// If the index isn't ready, wait for it, and search again when ready.
	if (!searchIndexReady) {
		resultsElem.append($('<a class="dropdown-item disabled">SEARCHING...</a>'));
		$(document).one('searchIndexReady', function() { doSearch(options); });
		return;
	}

	var query = options.query;
	var snippetLen = options.snippetLen;
	var limit = options.limit;

	if (query === '') { return; }

	var results = searchIndex.search(query, {
		fields: { title: {boost: 10}, text: { boost: 1 } },
		expand: true,
		bool: "AND"
	});

	var snippetBuilder = new SnippetBuilder(query);
	if (results.length > 0){
		var len = Math.min(results.length, limit || Infinity);
		for (var i = 0; i < len; i++) {
			var doc = searchIndex.documentStore.getDoc(results[i].ref);
			var snippet = snippetBuilder.getSnippet(doc.text, snippetLen);
			resultsElem.append(
				$('<a class="dropdown-item">').attr('href', limit == 0 ? doc.location : pathJoin(base_url, doc.location))
				.append($('<h6 class="dropdown-header">').text(doc.title))
				.append($('<p>').html(snippet))
			);
		}
		if (limit != 0) {
			resultsElem.find('a').each(function() { adjustLink(this); });
		}
		if (limit) {
			resultsElem.append($('<div class="dropdown-divider" role="separator"></div>'));
			resultsElem.append($(
				'<a class="dropdown-item" href="' + base_url + '/search.html?q=' + query + '" id="search-show-all" target="article">' +
				'SEE ALL RESULTS</a>'));
		}
	} else {
		resultsElem.append($('<a class="dropdown-item disabled">NO RESULTS FOUND</a>'));
	}
}

function pathJoin(prefix, suffix) {
	var nPrefix = endsWith(prefix, "/") ? prefix.slice(0, -1) : prefix;
	var nSuffix = startsWith(suffix, "/") ? suffix.slice(1) : suffix;
	return nPrefix + "/" + nSuffix;
}
