export function toggleFullscreen (elementId) {
	// https://www.w3schools.com/howto/howto_js_fullscreen.asp
	const elem = document.getElementById(elementId)
	if (document.fullscreenElement == null) {
		if (elem.requestFullscreen) {
			elem.requestFullscreen();
		} else if (elem.webkitRequestFullscreen) { /* Safari */
			elem.webkitRequestFullscreen();
		} else if (elem.msRequestFullscreen) { /* IE11 */
			elem.msRequestFullscreen();
		}
		return true
	} else {
		document.exitFullscreen();
		return false
	}
}