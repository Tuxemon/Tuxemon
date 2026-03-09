const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const statusEl = document.getElementById('status');
const nameInput = document.getElementById('nameInput');
const setNameBtn = document.getElementById('setName');

const wsPort = new URLSearchParams(window.location.search).get('wsPort') || '8765';
const wsUrl = `ws://${window.location.hostname}:${wsPort}`;

const state = {
  myId: null,
  players: {},
  keys: new Set(),
};

const socket = new WebSocket(wsUrl);

socket.addEventListener('open', () => {
  statusEl.textContent = `Connected: ${wsUrl}`;
});

socket.addEventListener('close', () => {
  statusEl.textContent = 'Disconnected';
});

socket.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'welcome') {
    state.myId = data.id;
  }
  if (data.type === 'state') {
    state.players = data.players || {};
  }
});

setNameBtn.addEventListener('click', () => {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;
  socket.send(JSON.stringify({ type: 'rename', name: nameInput.value }));
  nameInput.value = '';
});

window.addEventListener('keydown', (event) => {
  state.keys.add(event.key.toLowerCase());
});

window.addEventListener('keyup', (event) => {
  state.keys.delete(event.key.toLowerCase());
});

function sendMove() {
  const me = state.players[state.myId];
  if (!me || socket.readyState !== WebSocket.OPEN) return;

  let dx = 0;
  let dy = 0;
  if (state.keys.has('arrowleft') || state.keys.has('a')) dx -= 2;
  if (state.keys.has('arrowright') || state.keys.has('d')) dx += 2;
  if (state.keys.has('arrowup') || state.keys.has('w')) dy -= 2;
  if (state.keys.has('arrowdown') || state.keys.has('s')) dy += 2;

  if (dx === 0 && dy === 0) return;

  socket.send(
    JSON.stringify({
      type: 'move',
      x: me.x + dx,
      y: me.y + dy,
    }),
  );
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (const [id, player] of Object.entries(state.players)) {
    ctx.beginPath();
    ctx.fillStyle = player.color || '#fff';
    ctx.arc(player.x, player.y, id === state.myId ? 14 : 12, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#f8fafc';
    ctx.font = '12px sans-serif';
    const label = `${player.name}${id === state.myId ? ' (you)' : ''}`;
    ctx.fillText(label, player.x - 20, player.y - 18);
  }

  requestAnimationFrame(draw);
}

setInterval(sendMove, 16);
requestAnimationFrame(draw);
