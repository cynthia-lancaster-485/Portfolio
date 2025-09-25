import { NavLink, useNavigate } from "react-router";
import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from "./AuthContext";

const headerClassName = "text-center text-4xl font-extrabold py-4";

function Login() {
    const navigate = useNavigate();
    const { login } = useContext(AuthContext);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async(event) => {
        event.preventDefault();
        setIsSubmitting(true);
        setError('');

        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);


        try{
            const response = await fetch('http://127.0.0.1:8000/auth/web/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: formData.toString(),
            });
            if(!response.ok){
                const errorData = await response.json();
                console.log('Error response:', errorData);
                throw new Error(errorData.message || 'Invalid username or password'); 
            }
            const tokenResponse = await fetch('http://127.0.0.1:8000/auth/token', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: formData.toString(),
            });

            if(!tokenResponse.ok){
                throw new Error('Failed to get access token');
            }   
            const tokenData = await tokenResponse.json();
            const token = tokenData.access_token;
            login(token);
            navigate('/chats');
        }
        catch (error){
            setError(error.message);
        }
        finally {
            setIsSubmitting(false);
        }
    }

    const isFormValid = username.trim() !== "" && password.trim() !== "";

    return (
    
      <div>
         <h1 className={headerClassName}>Pony Express</h1>
         <div className="flex items-center justify-center">
            <form onSubmit={handleSubmit} className="p-8 bg-gray-200 rounded w-full max-w-sm space-y-6">
                <div className="flex flex-col">
                    <label htmlFor="username" className="mb-2 text-sm font-medium text-gray-700">Username</label>
                    <input 
                        type="text" 
                        id="username" 
                        name="username" 
                        value={username} 
                        onChange={(e) => setUsername(e.target.value)} 
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                        required>
                    </input>
                </div>

                <div className="flex flex-col">
                    <label htmlFor="password" className="mb-2 text-sm font-medium text-gray-700">Password</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                        required>
                    </input>
                </div>
                {error && <div className="text-red-500 text-sm">{error}</div>}
                <div>
                    <button
                        type="submit"
                        className={`w-full bg-blue-500 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded ${!isFormValid || isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
                        disabled={!isFormValid || isSubmitting}>
                            {isSubmitting ? 'Logging In...' : 'Log In'}
                    </button>
                </div>
                <div className="text-center m-4">
                    <button
                        onClick={() => navigate('/register')}
                        className="text-blue-500 hover:text-blue-700 text-sm">
                            Don't have an account? Register
                        </button>
                </div>
            </form>
        </div>
      </div>
    );
  }
  
  export default Login;