import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, signup } from '../api';

function Login() {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (isSignup) {
        await signup(email, password);
        setIsSignup(false);
        setError('Signup successful! Please log in.');
      } else {
        const res = await login(email, password);
        localStorage.setItem('access_token', res.data.access_token);
        localStorage.setItem('refresh_token', res.data.refresh_token);
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', fontFamily: 'Arial' }}>
      <h2>DrapeStudio Inventory</h2>
      <h3>{isSignup ? 'Sign Up' : 'Login'}</h3>

      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ display: 'block', width: '100%', padding: 8, marginBottom: 10 }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ display: 'block', width: '100%', padding: 8, marginBottom: 10 }}
        />
        <button type="submit" style={{ padding: '8px 16px' }}>
          {isSignup ? 'Sign Up' : 'Login'}
        </button>
      </form>

      {error && <p style={{ color: error.includes('successful') ? 'green' : 'red' }}>{error}</p>}

      <p style={{ marginTop: 15 }}>
        <button onClick={() => setIsSignup(!isSignup)} style={{ background: 'none', border: 'none', color: 'blue', cursor: 'pointer' }}>
          {isSignup ? 'Already have an account? Log in' : "Don't have an account? Sign up"}
        </button>
      </p>
    </div>
  );
}

export default Login;