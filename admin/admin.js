const API = 'http://localhost:5001/api';
const token = () => localStorage.getItem('campusfix_admin_token');
const byId = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const label = value => String(value || '').replaceAll('_', ' ').replace(/\b\w/g, char => char.toUpperCase());

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { ...options, headers: {'Content-Type': 'application/json', ...(options.headers || {}), ...(token() ? {'Authorization': `Bearer ${token()}`} : {})} });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}

const loginForm = byId('adminLoginForm');
if (loginForm) {
  const message = byId('adminMessage');
  const registerForm = byId('adminRegisterForm');
  const loginButton = loginForm.querySelector('button[type="submit"]');
  const registerButton = registerForm.querySelector('button[type="submit"]');
  byId('showRegister').onclick = () => { registerForm.hidden = false; byId('showRegister').hidden = true; };
  loginForm.onsubmit = async event => {
    event.preventDefault();
    loginButton.disabled = true;
    loginButton.textContent = 'Signing in...';
    message.textContent = '';
    try {
      const data = await request('/admin/login', {method: 'POST', body: JSON.stringify({email: byId('adminEmail').value.trim(), password: byId('adminPassword').value})});
      localStorage.setItem('campusfix_admin_token', data.token);
      localStorage.setItem('campusfix_admin', JSON.stringify(data.admin));
      location.href = 'dashboard.html';
    } catch (error) {
      console.error('[ADMIN AUTH] Login failed:', error);
      message.textContent = error.message === 'Invalid admin credentials' ? 'Invalid email or password.' : error.message;
    } finally { loginButton.disabled = false; loginButton.textContent = 'Sign In'; }
  };
  registerForm.onsubmit = async event => {
    event.preventDefault();
    registerButton.disabled = true;
    registerButton.textContent = 'Creating account...';
    message.textContent = '';
    try {
      await request('/admin/register', {method: 'POST', body: JSON.stringify({name: byId('adminName').value.trim(), email: byId('adminEmail').value.trim(), password: byId('adminPassword').value, registration_code: byId('adminCode').value})});
      message.textContent = 'Account created. Sign in above.';
      registerForm.reset();
    } catch (error) {
      console.error('[ADMIN AUTH] Signup failed:', error);
      message.textContent = error.message;
    } finally { registerButton.disabled = false; registerButton.textContent = 'Create Account'; }
  };
}

const ticketRows = byId('ticketRows');
if (ticketRows) {
  if (!token()) location.replace('login.html');
  let tickets = [];
  let users = [];
  const toast = text => { const element = byId('toast'); element.textContent = text; element.classList.add('show'); setTimeout(() => element.classList.remove('show'), 2500); };
  const renderBars = (id, values = {}) => { const element = byId(id); if (!element) return; const max = Math.max(...Object.values(values), 1); element.innerHTML = Object.entries(values).map(([name, value]) => `<div class="admin-bar-row"><span>${esc(label(name))}</span><div><i style="width:${value ? Math.max((value / max) * 100, 4) : 0}%"></i></div><b>${value}</b></div>`).join('') || '<p class="admin-muted">No data available.</p>'; };
  const stats = data => { byId('adminStats').innerHTML = [['Total Users', data.total_users], ['Students', data.students], ['Faculty', data.employees], ['Total Tickets', data.total], ['Open', data.open], ['High Priority', data.high_priority], ['Resolved', data.resolved], ['AI Escalations', data.human_escalations]].map(item => `<div class="admin-stat"><span>${item[0]}</span><b>${item[1] ?? 0}</b></div>`).join(''); byId('aiPerformance').innerHTML = `<div><span>Total conversations</span><b>${data.total_conversations ?? 'N/A'}</b></div><div><span>Human escalations</span><b>${data.human_escalations ?? 'N/A'}</b></div><div><span>AI resolution rate</span><b>${data.ai_resolution_rate == null ? 'N/A' : `${data.ai_resolution_rate}%`}</b></div>`; renderBars('categoryChart', data.category_counts); renderBars('priorityChart', data.priority_counts); renderBars('statusChart', data.status_counts); };
  const renderTickets = () => { const search = byId('ticketSearch').value.toLowerCase(); const list = tickets.filter(ticket => (!search || `${ticket.ticket_id} ${ticket.username} ${ticket.issue}`.toLowerCase().includes(search)) && (!byId('statusFilter').value || ticket.status === byId('statusFilter').value) && (!byId('priorityFilter').value || ticket.priority === byId('priorityFilter').value) && (!byId('categoryFilter').value || ticket.category === byId('categoryFilter').value)); ticketRows.innerHTML = list.map(ticket => `<tr><td><strong>${esc(ticket.ticket_id)}</strong></td><td>${esc(ticket.username)}</td><td>${esc(label(ticket.user_type))}</td><td>${esc(ticket.issue)}</td><td>${esc(label(ticket.category))}</td><td>${esc(label(ticket.priority))}</td><td>${esc(ticket.assigned_admin || ticket.assigned_team || ticket.department)}</td><td>${esc(label(ticket.status))}</td><td>${esc(new Date(ticket.created_at).toLocaleDateString())}</td><td><button class="table-action" data-id="${esc(ticket.ticket_id)}">View</button></td></tr>`).join('') || '<tr><td colspan="10">No tickets found.</td></tr>'; ticketRows.querySelectorAll('[data-id]').forEach(button => button.onclick = () => showDetail(button.dataset.id)); };
  const renderUsers = () => { const search = byId('userSearch').value.toLowerCase(); const type = byId('userTypeFilter').value; const list = users.filter(user => (!type || user.usertype === type) && (!search || `${user.username} ${user.email} ${user.registration_number || user.employee_id || ''}`.toLowerCase().includes(search))); byId('userRows').innerHTML = list.map(user => `<tr><td>${esc(user.username)}</td><td>${esc(label(user.usertype))}</td><td>${esc(user.registration_number || user.employee_id || 'N/A')}</td><td>${esc(user.email)}</td><td>${esc(user.department || 'N/A')}</td><td>${esc(user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A')}</td></tr>`).join('') || '<tr><td colspan="6">No users found.</td></tr>'; };
  const showDetail = async id => { try { const ticket = (await request(`/admin/tickets/${encodeURIComponent(id)}`)).ticket; const identifier = ticket.user_type === 'employee' ? ticket.employee_id : ticket.registration_number; const detail = byId('ticketDetail'); detail.hidden = false; detail.innerHTML = `<div class="admin-detail"><h2>${esc(ticket.ticket_id)}</h2><p><strong>User:</strong> ${esc(ticket.username)} | <strong>Type:</strong> ${esc(label(ticket.user_type))} | <strong>ID:</strong> ${esc(identifier || 'N/A')} | <strong>Email:</strong> ${esc(ticket.email)}</p><p><strong>Issue:</strong> ${esc(ticket.issue)} | <strong>Category:</strong> ${esc(label(ticket.category))}</p><p><strong>Description:</strong> ${esc(ticket.description)}</p><p><strong>AI Summary:</strong> ${esc(ticket.ai_summary)}</p><p><strong>Troubleshooting:</strong> ${esc((ticket.troubleshooting_attempted || []).join(' | '))}</p><div class="admin-detail-grid"><label>Status<select id="editStatus"><option>open</option><option>assigned</option><option>in_progress</option><option>waiting_for_user</option><option>resolved</option><option>closed</option></select></label><label>Priority<select id="editPriority"><option>low</option><option>medium</option><option>high</option><option>critical</option></select></label><label>Team<select id="editTeam"><option>Network Support</option><option>Hardware Support</option><option>Software Support</option><option>Account Support</option><option>General IT Support</option></select></label><label>Assigned Admin<input id="editAdmin" value="${esc(ticket.assigned_admin || '')}"></label></div><p><strong>Timeline:</strong> ${esc((ticket.timeline || []).map(item => item.event).join(' | '))}</p><p><strong>Notes:</strong> ${esc((ticket.admin_notes || []).map(item => item.note).join(' | ') || 'None')}</p><textarea id="editNote" placeholder="Add an administrator note"></textarea><button class="admin-primary" id="saveTicket">Save ticket</button></div>`; byId('editStatus').value = ticket.status; byId('editPriority').value = ticket.priority; byId('editTeam').value = ticket.assigned_team || ticket.department; byId('saveTicket').onclick = async () => { try { await request(`/admin/tickets/${encodeURIComponent(id)}`, {method: 'PATCH', body: JSON.stringify({status: byId('editStatus').value, priority: byId('editPriority').value, assigned_team: byId('editTeam').value, assigned_admin: byId('editAdmin').value, note: byId('editNote').value})}); toast('Ticket updated'); await load(); await showDetail(id); } catch (error) { toast('Unable to update ticket'); } }; } catch (error) { toast('Unable to load ticket details'); } };
  const load = async () => { try { const [dashboardStats, ticketData, userData] = await Promise.all([request('/admin/stats'), request('/admin/tickets'), request('/admin/users')]); tickets = ticketData.tickets || []; users = userData.users || []; stats(dashboardStats); renderTickets(); renderUsers(); byId('facultyRows').innerHTML = users.filter(user => user.usertype === 'employee').map(user => `<tr><td>${esc(user.username)}</td><td>${esc(user.employee_id || 'N/A')}</td><td>${esc(user.department || 'N/A')}</td><td>${esc(user.email)}</td><td>${tickets.filter(ticket => ticket.user_id === String(user._id)).length}</td><td>${esc(user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A')}</td></tr>`).join('') || '<tr><td colspan="6">No faculty accounts found.</td></tr>'; byId('activityFeed').innerHTML = tickets.slice(0, 6).map(ticket => `<div class="admin-feed-item"><span class="feed-dot"></span><div><strong>${esc(ticket.ticket_id)} · ${esc(label(ticket.status))}</strong><p>${esc(ticket.issue)}</p></div></div>`).join('') || '<p>No activity available.</p>'; byId('notificationFeed').innerHTML = tickets.filter(ticket => ['high','critical'].includes(ticket.priority) || ['resolved','closed'].includes(ticket.status)).slice(0, 8).map(ticket => `<div class="admin-feed-item"><span class="feed-dot"></span><div><strong>${esc(ticket.ticket_id)}</strong><p>${esc(ticket.issue)}</p></div></div>`).join('') || '<p>No notifications.</p>'; byId('notificationCount').textContent = tickets.filter(ticket => ['high','critical'].includes(ticket.priority)).length; byId('escalationRows').innerHTML = tickets.filter(ticket => ticket.conversation_id).map(ticket => `<tr><td>${esc(ticket.ticket_id)}</td><td>${esc(ticket.username)}</td><td>${esc(ticket.issue)}</td><td>${esc(ticket.ai_summary)}</td><td>${esc((ticket.troubleshooting_attempted || []).join(', '))}</td><td>${esc(label(ticket.priority))}</td><td>${esc(label(ticket.status))}</td><td>${esc(new Date(ticket.created_at).toLocaleDateString())}</td><td><button class="table-action" data-id="${esc(ticket.ticket_id)}">View</button></td></tr>`).join('') || '<tr><td colspan="9">No AI escalations currently.</td></tr>'; byId('escalationRows').querySelectorAll('[data-id]').forEach(button => button.onclick = () => showDetail(button.dataset.id)); } catch (error) { console.error('[ADMIN] Dashboard load failed:', error); ticketRows.innerHTML = '<tr><td colspan="10">Unable to load dashboard. Check the backend connection.</td></tr>'; } };
  document.querySelectorAll('.admin-nav').forEach(button => button.onclick = () => { document.querySelectorAll('.admin-nav').forEach(item => item.classList.remove('active')); document.querySelectorAll('.admin-view').forEach(view => view.classList.remove('active')); button.classList.add('active'); document.querySelector(`[data-view="${button.dataset.section}"]`).classList.add('active'); });
  [byId('ticketSearch'), byId('statusFilter'), byId('priorityFilter'), byId('categoryFilter')].forEach(input => input.oninput = renderTickets); [byId('userSearch'), byId('userTypeFilter')].forEach(input => input.oninput = renderUsers); document.querySelectorAll('[data-refresh]').forEach(button => button.onclick = load); byId('refreshButton').onclick = load; byId('notificationButton').onclick = () => document.querySelector('[data-section="notifications"]').click(); byId('adminLogout').onclick = () => { localStorage.removeItem('campusfix_admin_token'); localStorage.removeItem('campusfix_admin'); location.href = 'login.html'; }; byId('adminMenu').onclick = () => byId('adminSidebar').classList.toggle('open'); byId('adminNameDisplay').textContent = JSON.parse(localStorage.getItem('campusfix_admin') || '{}').name || 'Administrator'; load(); setInterval(load, 60000);
}
