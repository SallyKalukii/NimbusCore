// Get login type from URL
const urlParams = new URLSearchParams(window.location.search);
const loginType = urlParams.get('type') || 'user';

// Update UI based on login type
document.addEventListener('DOMContentLoaded', () => {
    const loginTypeElement = document.getElementById('login-type');
    if (loginType === 'admin') {
        loginTypeElement.textContent = 'Admin Access Only';
        loginTypeElement.style.background = '#E0115F';
    } else {
        loginTypeElement.textContent = 'User Login';
        loginTypeElement.style.background = '#808080';
    }
});

// Handle login
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('error-message');
    
    try {
        // Sign in with Firebase
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        // Get user role from Firestore
        const userDoc = await db.collection('users').doc(user.uid).get();
        
        if (!userDoc.exists) {
            throw new Error('User profile not found');
        }
        
        const userData = userDoc.data();
        const userRole = userData.role;
        
        // Check if role matches login type
        if (loginType === 'admin' && userRole !== 'admin') {
            await auth.signOut();
            showError('Access denied. Admin credentials required.');
            return;
        }
        
        // Redirect based on role
        if (userRole === 'admin') {
            window.location.href = 'admin-dashboard.html';
        } else {
            window.location.href = 'user-dashboard.html';
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showError(getErrorMessage(error.code));
    }
});

function showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

function getErrorMessage(code) {
    switch (code) {
        case 'auth/invalid-email':
            return 'Invalid email address format.';
        case 'auth/user-not-found':
            return 'No account found with this email.';
        case 'auth/wrong-password':
            return 'Incorrect password.';
        case 'auth/too-many-requests':
            return 'Too many failed attempts. Please try again later.';
        default:
            return 'Login failed. Please check your credentials.';
    }
}

// Check if already logged in
auth.onAuthStateChanged(async (user) => {
    if (user && window.location.pathname.includes('login.html')) {
        const role = await getUserRole(user.uid);
        if (role === 'admin') {
            window.location.href = 'admin-dashboard.html';
        } else {
            window.location.href = 'user-dashboard.html';
        }
    }
});