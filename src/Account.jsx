import { NavLink, useNavigate } from "react-router";
import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from "./AuthContext";

const headerClassName = "text-center text-4xl font-extrabold py-4";

function Account() {
    const [username, setUsername] = useState('');
    const { token } = useContext(AuthContext);
    const navigate = useNavigate();
    const { logout } = useContext(AuthContext);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchUserData = async () => {
            if(!token) {
                console.error('No token found');
                return;
            }
            try {
                const response = await fetch('http://127.0.0.1:8000/accounts/me', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                });
                if(response.ok){
                    const user = await response.json();
                    setUsername(user.username);
                }
                else {
                    console.error('Failed to get user data')
                }
            }
            catch (error){
                console.error('Error fetching user data:', error);
            }
        };
        fetchUserData();
    }, [token]);

    const handleLogout = async () => {
        setIsSubmitting(true);
        setError('');
        try {
            const response = await fetch('http://127.0.0.1:8000/auth/web/logout', {
                method: 'POST',
                credentials: 'include',
            });
            if(response.ok) {
                throw new Error('Failed to log out');
            }

            logout();
            navigate('/auth/web/login');
        }
        catch (error){
            setError(error.message || "Could not logout");
        }
        finally {
            setIsSubmitting(false);
        }
    }

    return (
    
      <div>
         <h1 className={headerClassName}>Settings</h1>
         <div className="space-y-2">
            <h3><strong>{username}</strong></h3>
            <button className={`w-full hover:bg-black hover:text-white font-semibold px-4 rounded ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
                onClick={handleLogout}
                disabled={isSubmitting}>
                Logout
            </button>
            <NavLink
                to="/accounts/me"
                end
                className={({ isActive }) =>
                    `block px-4 rounded 
                    ${isActive 
                        ? "bg-blue-500 text-white font-bold"
                        : "hover:bg-black hover:text-white"}`
                }
            >
                Update Account
            </NavLink>
            <NavLink
                to="/accounts/me/password"
                className={({ isActive }) =>
                    `block px-4 rounded 
                    ${isActive 
                        ? "bg-blue-500 text-white font-bold"
                        : "hover:bg-black hover:text-white"}`
                }
            >
                Update Password
            </NavLink>
            <NavLink
                to="/accounts/manage"
                className={({ isActive }) =>
                    `block px-4 rounded 
                    ${isActive 
                        ? "bg-blue-500 text-white font-bold"
                        : "hover:bg-black hover:text-white"}`
                }
            >
                Manage Account
            </NavLink>
         </div>
      </div>
    );
  }
  
  export default Account;