export function submitPostRequest(url, headers, operation, payload, callback) {
  const body = JSON.stringify({
    operation: operation,
    payload: payload,
  });
  fetch(url, {
    method: 'POST',
    headers: headers,
    body: body,
  })
    .then((response) => response.json())
    .then((result) => {
      if (callback) {
        callback(result);
      }
    });
}

export function getFromAPI(url, headers, callback) {
  fetch(url, {
    method: 'GET',
    headers: headers,
  })
    .then((response) => response.json())
    .then((result) => {
      if (callback) {
        callback(result);
      }
    });
}
