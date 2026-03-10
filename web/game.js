const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const statusEl = document.getElementById('status');
const nameInput = document.getElementById('nameInput');
const setNameBtn = document.getElementById('setName');
const scoreEl = document.getElementById('scoreboard');

const wsPort = new URLSearchParams(window.location.search).get('wsPort') || '8765';
const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const wsUrl = `${wsProtocol}://${window.location.hostname}:${wsPort}`;

const state = {
  myId: null,
  players: {},
  collectibles: [],
  winner: null,
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
    state.collectibles = data.collectibles || [];
    state.winner = data.winner || null;
    renderScoreboard();
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

function renderScoreboard() {
  const players = Object.entries(state.players)
    .sort(([, a], [, b]) => (b.score || 0) - (a.score || 0))
    .slice(0, 5);

  scoreEl.innerHTML = players
    .map(([id, player]) => {
      const you = id === state.myId ? ' (you)' : '';
      return `<li><span>${player.name}${you}</span><strong>${player.score || 0}</strong></li>`;
    })
    .join('');
}

function sendMove() {
  const me = state.players[state.myId];
  if (!me || socket.readyState !== WebSocket.OPEN || state.winner) return;

  let dx = 0;
  let dy = 0;
  if (state.keys.has('arrowleft') || state.keys.has('a')) dx -= 3;
  if (state.keys.has('arrowright') || state.keys.has('d')) dx += 3;
  if (state.keys.has('arrowup') || state.keys.has('w')) dy -= 3;
  if (state.keys.has('arrowdown') || state.keys.has('s')) dy += 3;

  if (dx === 0 && dy === 0) return;

  socket.send(
    JSON.stringify({
      type: 'move',
      x: me.x + dx,
      y: me.y + dy,
    }),
  );
}

function drawArena() {
  ctx.fillStyle = '#0b1020';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 2;
  ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);
}

function drawCollectibles() {
  for (const item of state.collectibles) {
    ctx.beginPath();
    ctx.fillStyle = '#facc15';
    ctx.arc(item.x, item.y, 7, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawPlayers() {
  for (const [id, player] of Object.entries(state.players)) {
    ctx.beginPath();
    ctx.fillStyle = player.color || '#fff';
    ctx.arc(player.x, player.y, id === state.myId ? 14 : 12, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#f8fafc';
    ctx.font = '12px sans-serif';
    const label = `${player.name}${id === state.myId ? ' (you)' : ''} • ${player.score || 0}`;
    ctx.fillText(label, player.x - 30, player.y - 18);
  }
}

function drawWinnerBanner() {
  if (!state.winner) return;

  ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
  ctx.fillRect(180, 210, 440, 80);
  ctx.strokeStyle = '#22c55e';
  ctx.lineWidth = 2;
  ctx.strokeRect(180, 210, 440, 80);

  ctx.fillStyle = '#e2e8f0';
  ctx.font = 'bold 24px sans-serif';
  ctx.fillText(`${state.winner.name} wins with ${state.winner.score} points!`, 210, 258);
}

function draw() {
  drawArena();
  drawCollectibles();
  drawPlayers();
  drawWinnerBanner();
  requestAnimationFrame(draw);
}

setInterval(sendMove, 16);
requestAnimationFrame(draw);
