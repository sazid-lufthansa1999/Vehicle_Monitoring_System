import React, { useState } from 'react';
import { auth } from '../firebase/config';
import { signInWithEmailAndPassword, signInWithPopup, signInWithRedirect, GoogleAuthProvider } from 'firebase/auth';
import { Activity, Mail, Lock, LogIn } from 'lucide-react';

function Login({ onLogin }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await signInWithEmailAndPassword(auth, email, password);
        } catch (err) {
            setError('Invalid credentials. Please check your email/password.');
            console.error(err);
        }
        setLoading(false);
    };

    const handleGoogleLogin = async () => {
        setError('');
        setLoading(true);
        const provider = new GoogleAuthProvider();
        // Force Google to show the account selection screen every time
        provider.setCustomParameters({
            prompt: 'select_account'
        });

        try {
            await signInWithPopup(auth, provider);
        } catch (err) {
            console.error("Google Auth Error:", err);
            setError(err.code === 'auth/popup-blocked'
                ? 'Popup blocked! Please allow popups for this site.'
                : (err.message || 'Google sign-in failed.'));
        }
        setLoading(false);
    };

    return (
        <div className="h-screen w-full flex items-center justify-center bg-dark selection:bg-accent/30">
            <div className="w-full max-w-md p-8 glass rounded-[40px] border border-white/10 shadow-2xl animate-in fade-in zoom-in duration-500">
                <div className="flex flex-col items-center mb-10">
                    <div className="w-16 h-16 bg-accent rounded-2xl flex items-center justify-center shadow-xl shadow-accent/20 mb-6">
                        <Activity className="text-dark w-8 h-8" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight">AI Vision Pro</h1>
                    <p className="text-gray-500 mt-2 text-sm font-medium uppercase tracking-[0.2em]">Management Portal</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-5">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-gray-500 uppercase tracking-widest ml-1">Email Address</label>
                        <div className="relative group">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-accent transition-colors" size={18} />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-accent/50 focus:bg-white/10 transition-all text-sm font-medium text-white placeholder:text-gray-600"
                                placeholder="name@company.com"
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-bold text-gray-500 uppercase tracking-widest ml-1">Secret Key</label>
                        <div className="relative group">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-accent transition-colors" size={18} />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-accent/50 focus:bg-white/10 transition-all text-sm font-medium text-white placeholder:text-gray-600"
                                placeholder="••••••••"
                                required
                            />
                        </div>
                    </div>

                    {error && (
                        <div className="p-4 bg-danger/10 border border-danger/20 rounded-xl text-danger text-xs font-bold text-center">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-accent text-dark font-black py-4 rounded-2xl shadow-lg shadow-accent/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-3 mt-4"
                    >
                        {loading ? 'AUTHENTICATING...' : <><LogIn size={18} /> SIGN IN</>}
                    </button>
                </form>

                <div className="relative my-8">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-white/10"></div>
                    </div>
                    <div className="relative flex justify-center text-[10px] uppercase font-bold tracking-widest">
                        <span className="bg-[#0f172a] px-4 text-gray-500">Or continue with</span>
                    </div>
                </div>

                <button
                    onClick={handleGoogleLogin}
                    disabled={loading}
                    className="w-full bg-white/5 border border-white/10 text-white font-bold py-4 rounded-2xl hover:bg-white/10 hover:border-white/20 transition-all flex items-center justify-center gap-3"
                >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                        <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                        <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    Google Account
                </button>

                <div className="mt-8 text-center">
                    <p className="text-gray-600 text-[10px] font-bold uppercase tracking-widest">
                        Protected by Bio-Security Layer v4.0
                    </p>
                </div>
            </div>
        </div>
    );
}

export default Login;
