const form = document.querySelector('#download-form'),
  input = document.querySelector('#youtube-url'),
  button = document.querySelector('#download-button'),
  statusBox = document.querySelector('#status'),
  statusText = document.querySelector('#status-text'),
  bar = document.querySelector('#bar-fill'),
  percent = document.querySelector('#percent'),
  details = document.querySelector('#details'),
  fileLink = document.querySelector('#file-link'),
  error = document.querySelector('#error'),
  csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;

function showState(data) {
  const value = data.progress ?? 0;
  bar.style.width = `${value}%`;
  bar.parentElement.setAttribute('aria-valuenow', value);
  percent.textContent = `${value}%`;
  details.textContent = [
    data.downloaded && `Téléchargé : ${data.downloaded}${data.total ? ` / ${data.total}` : ''}`,
    data.speed && `Vitesse : ${data.speed}/s`,
    data.eta && `Temps restant : ${data.eta}`
  ].filter(Boolean).join(' · ');

  if (data.status === 'completed') {
    statusText.textContent = '✓ Traitement terminé ! Téléchargement dans votre navigateur…';
  } else if (data.status === 'queued') {
    statusText.textContent = 'Préparation du téléchargement…';
  } else {
    statusText.textContent = 'Téléchargement…';
  }
}

async function poll(id) {
  const response = await fetch(`/progress/${id}/`),
    data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Impossible de récupérer la progression.');

  showState(data);

  if (data.status === 'completed') {
    button.disabled = false;
    button.textContent = 'Télécharger une autre vidéo';
    if (data.download_url) {
      fileLink.href = data.download_url;
      fileLink.hidden = false;

      // Automatically trigger browser download on user device
      const a = document.createElement('a');
      a.href = data.download_url;
      a.download = '';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
    return;
  }
  if (data.status === 'error') throw new Error(data.error);

  window.setTimeout(() => poll(id).catch(fail), 800);
}

function fail(reason) {
  error.textContent = reason.message || 'Impossible de télécharger cette vidéo.';
  button.disabled = false;
  button.textContent = 'Télécharger';
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  error.textContent = '';
  fileLink.hidden = true;
  statusBox.hidden = false;
  showState({ status: 'queued', progress: 0 });
  button.disabled = true;
  button.textContent = 'Téléchargement…';

  try {
    const response = await fetch('/download/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify({ url: input.value })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Impossible de démarrer le téléchargement.');
    poll(data.download_id).catch(fail);
  } catch (reason) {
    fail(reason);
  }
});
