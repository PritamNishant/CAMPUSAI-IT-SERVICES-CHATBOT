/* ================================
   CAMPUS FIX AI - Ticket Management
   ================================ */

// Initialize ticket functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTicketing();
});

/**
 * Initialize ticket modal functionality
 */
function initializeTicketing() {
    const ticketForm = document.getElementById('ticketForm');
    
    if (ticketForm) {
        ticketForm.addEventListener('submit', handleTicketSubmission);
    }
    
    // Pre-fill ticket form if conversation state has info
    prefillTicketForm();
}

async function loadMyTickets() {
    const section = document.getElementById('my-tickets');
    const list = document.getElementById('myTicketsList');
    const token = localStorage.getItem('campusfix_token');
    if (!section || !list || !token) return;
    section.style.display = 'block';
    list.innerHTML = '<p>Loading tickets...</p>';
    try {
        const response = await fetch('http://localhost:5001/api/tickets/my', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Unable to load tickets');
        if (!data.tickets.length) {
            list.innerHTML = '<p>No support tickets yet.</p>';
            section.scrollIntoView({ behavior: 'smooth' });
            return;
        }
        list.innerHTML = data.tickets.map(ticket => `
            <article class="my-ticket-card">
                <div><strong>${escapeHtml(ticket.ticket_id)}</strong><p>${escapeHtml(ticket.issue || '')}</p></div>
                <span class="ticket-status">${escapeHtml((ticket.status || '').replaceAll('_', ' ').toUpperCase())}</span>
                <span>${escapeHtml((ticket.priority || '').toUpperCase())}</span>
                <span>${escapeHtml(ticket.assigned_team || ticket.department || 'Unassigned')}</span>
                <time>${escapeHtml(new Date(ticket.created_at).toLocaleDateString())}</time>
                <details><summary>View details</summary><p>${escapeHtml(ticket.ai_summary || '')}</p><ul>${(ticket.timeline || []).map(item => `<li>${escapeHtml(item.event)} - ${escapeHtml(new Date(item.at || item.timestamp).toLocaleString())}</li>`).join('')}</ul></details>
            </article>
        `).join('');
        section.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        list.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
    }
}

/**
 * Open ticket creation modal
 */
function openTicketModal() {
    const modal = document.getElementById('ticketModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Pre-fill form with conversation context
        prefillTicketForm();
        
        // Focus on first input
        const firstInput = modal.querySelector('#ticketIssue');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

/**
 * Close ticket modal
 */
function closeTicketModal() {
    const modal = document.getElementById('ticketModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/**
 * Pre-fill ticket form with conversation data
 */
function prefillTicketForm() {
    const state = getConversationState();
    
    if (!state) return;
    
    const ticketIssue = document.getElementById('ticketIssue');
    const ticketCategory = document.getElementById('ticketCategory');
    const ticketDescription = document.getElementById('ticketDescription');
    const ticketLocation = document.getElementById('ticketLocation');
    
    // Set issue summary
    if (ticketIssue && state.issue) {
        ticketIssue.value = state.issue;
    }
    
    // Set category
    if (ticketCategory && state.category) {
        const categoryMap = {
            'wifi': 'wifi',
            'login': 'login',
            'software': 'software',
            'printer': 'printer',
            'unknown': 'other'
        };
        
        const category = categoryMap[state.category] || 'other';
        ticketCategory.value = category;
    }
    
    // Set description from conversation history
    if (ticketDescription && state.conversationHistory && state.conversationHistory.length > 0) {
        let description = 'Conversation Summary:\n\n';
        
        state.conversationHistory.slice(0, 6).forEach(msg => {
            const role = msg.role === 'user' ? 'User' : 'Fixie';
            description += `${role}: ${msg.content}\n\n`;
        });
        
        if (state.conversationHistory.length > 6) {
            description += '... (conversation continues)';
        }
        
        ticketDescription.value = description;
    }
    
    // Set location if available
    if (ticketLocation && state.location) {
        ticketLocation.value = state.location;
    }
}

/**
 * Handle ticket form submission
 */
async function handleTicketSubmission(e) {
    e.preventDefault();
    
    const token = localStorage.getItem('campusfix_token');
    if (!token) {
        alert('Please login to create a ticket.');
        if (typeof openAuthModal === 'function') {
            openAuthModal();
        }
        return;
    }
    
    const state = getConversationState();
    
    const formData = {
        issue: document.getElementById('ticketIssue').value,
        category: document.getElementById('ticketCategory').value,
        description: document.getElementById('ticketDescription').value,
        priority: document.getElementById('ticketPriority').value,
        location: document.getElementById('ticketLocation').value,
        conversation_id: state?.conversation_id
    };
    
    // Validate form
    if (!formData.issue || !formData.category || !formData.description) {
        alert('Please fill in all required fields.');
        return;
    }
    
    // Show loading state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating ticket...';
    }
    
    try {
        // Send to backend API
        const response = await fetch('http://localhost:5001/api/tickets/create', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create ticket');
        }
        
        const data = await response.json();
        const ticket = data.ticket;
        
        // Close ticket modal
        closeTicketModal();
        
        // Show success modal
        showTicketSuccessModal({
            id: ticket.ticket_id,
            issue: formData.issue,
            category: formData.category,
            description: formData.description,
            priority: ticket.priority,
            location: formData.location,
            status: ticket.status,
            department: ticket.department,
            created: ticket.created_at,
            assignedTo: ticket.assigned_team || ticket.department || 'Unassigned'
        });
        
        // Update conversation state
        if (state) {
            state.ticketCreated = true;
        }
        
    } catch (error) {
        console.error('Error creating ticket:', error);
        alert('Failed to create ticket. Please try again.');
    } finally {
        // Reset button state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Ticket';
        }
    }
}

/**
 * Generate a mock ticket for demonstration
 */
function generateMockTicket(formData) {
    const ticketId = `IT-2026-${Math.floor(Math.random() * 90000) + 10000}`;
    
    const categoryDepartments = {
        'wifi': 'Network Support',
        'login': 'Account Services',
        'software': 'Software Support',
        'printer': 'Hardware Support',
        'hardware': 'Hardware Support',
        'other': 'General IT Support'
    };
    
    const department = categoryDepartments[formData.category] || 'General IT Support';
    
    return {
        id: ticketId,
        issue: formData.issue,
        category: formData.category,
        description: formData.description,
        priority: formData.priority,
        location: formData.location,
        status: 'Assigned',
        department: department,
        created: new Date().toISOString(),
        assignedTo: 'IT Support Team'
    };
}

/**
 * Show ticket success modal
 */
function showTicketSuccessModal(ticket) {
    const modal = document.getElementById('ticketSuccessModal');
    
    if (!modal) return;
    
    // Update ticket details in modal
    const ticketIdElement = document.getElementById('successTicketId');
    const departmentElement = document.getElementById('successDepartment');
    const statusElement = document.getElementById('successTicketStatus');
    
    if (ticketIdElement) {
        ticketIdElement.textContent = ticket.id;
    }
    
    if (departmentElement) {
        departmentElement.textContent = ticket.department;
    }
    if (statusElement) {
        statusElement.textContent = String(ticket.status || 'open').replaceAll('_', ' ');
    }
    
    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Close ticket success modal
 */
function closeTicketSuccessModal() {
    const modal = document.getElementById('ticketSuccessModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Make functions globally available
window.openTicketModal = openTicketModal;
window.loadMyTickets = loadMyTickets;
window.closeTicketModal = closeTicketModal;
window.closeTicketSuccessModal = closeTicketSuccessModal;
