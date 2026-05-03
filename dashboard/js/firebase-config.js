// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyCYxpoNniurCmJYNi7u6YDo1vmE0Jld09Y",
    authDomain: "capstone-log-monitoring.firebaseapp.com",
    projectId: "capstone-log-monitoring",
    storageBucket: "capstone-log-monitoring.firebasestorage.app",
    messagingSenderId: "832448500331",
    appId: "1:832448500331:web:b8ae83753a9fb62521172e"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();
const auth = firebase.auth();

// ============================================
// HARDCODED ADMIN CREDENTIALS (Backend)
// ============================================
const ADMIN_CREDENTIALS = [
    {
        email: "sallymutemwa@gmail.com",
        password: "admin#1122",
        displayName: "Sally Mutemwa"
    },
    {
        email: "kinaropurity@gmail.com", 
        password: "Admin@2026!Secure",
        displayName: "Purity Kinaro"
    }
];

// User roles
const ROLES = {
    ADMIN: 'admin',
    USER: 'user'
};

// ============================================
// AUTO-CREATE ADMIN ACCOUNTS ON FIRST RUN
// ============================================
async function ensureAdminAccountsExist() {
    try {
        for (const adminCred of ADMIN_CREDENTIALS) {
            // Check if user already exists in Firestore
            const usersRef = db.collection('users');
            const existingUser = await usersRef
                .where('email', '==', adminCred.email)
                .limit(1)
                .get();
            
            if (existingUser.empty) {
                console.log(`Creating admin account: ${adminCred.email}`);
                
                // Create the Firebase Auth user
                try {
                    const userCredential = await auth.createUserWithEmailAndPassword(
                        adminCred.email, 
                        adminCred.password
                    );
                    
                    // Create Firestore user document
                    await db.collection('users').doc(userCredential.user.uid).set({
                        email: adminCred.email,
                        displayName: adminCred.displayName,
                        role: 'admin',
                        status: 'active',
                        createdAt: new Date().toISOString(),
                        lastLogin: null
                    });
                    
                    console.log(` Admin account created: ${adminCred.email}`);
                    
                    // Sign out after creating (we're just setting up)
                    await auth.signOut();
                    
                } catch (authError) {
                    // Account might already exist in Auth but not Firestore
                    if (authError.code === 'auth/email-already-in-use') {
                        console.log(`Admin account already exists in Auth: ${adminCred.email}`);
                    } else {
                        console.error('Error creating admin:', authError);
                    }
                }
            } else {
                console.log(`Admin account already exists: ${adminCred.email}`);
            }
        }
    } catch (error) {
        console.error('Error ensuring admin accounts:', error);
    }
}

// Run on page load to ensure admins exist
ensureAdminAccountsExist();

// Helper: Get current user
async function getCurrentUser() {
    return new Promise((resolve, reject) => {
        const unsubscribe = auth.onAuthStateChanged(user => {
            unsubscribe();
            resolve(user);
        }, reject);
    });
}

// Helper: Get user role
async function getUserRole(uid) {
    try {
        const userDoc = await db.collection('users').doc(uid).get();
        if (userDoc.exists) {
            return userDoc.data().role;
        }
        return null;
    } catch (error) {
        console.error('Error getting user role:', error);
        return null;
    }
}

// Helper: Check if admin
async function isAdmin() {
    const user = await getCurrentUser();
    if (!user) return false;
    const role = await getUserRole(user.uid);
    return role === ROLES.ADMIN;
}

// Helper: Check if email is authorized admin
function isAuthorizedAdmin(email) {
    return ADMIN_CREDENTIALS.some(admin => admin.email === email);
}

// Helper: Format timestamp
function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return timestamp;
    }
}

// Helper: Format time ago
function timeAgo(timestamp) {
    if (!timestamp) return 'N/A';
    
    const now = new Date();
    const past = new Date(timestamp);
    const diffMs = now - past;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
}