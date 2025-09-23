import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from './AuthContext';

const headerClassName = "text-center text-4xl font-extrabold py-4";

function ManageAccount() {
    const navigate = useNavigate();
    const { logout } = useContext(AuthContext);
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { token } = useContext(AuthContext);

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

    const handleDeleteAccount = async () => {
        setIsSubmitting(true);
        setError('');
        try {
            const response = await fetch('http://127.0.0.1:8000/accounts/me', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                credentials: 'include',
            });
            if(!response.ok){
                throw new Error('Failed to delete account');
            }
            logout();
            navigate('/login');
        }
        catch (error){
            setError(error.message || 'Could not delete account'); 
        }
        finally {
            setIsSubmitting(false);
        }
    }

    const isFormValid = !isSubmitting;

    return (
    
      <div>
         <h1 className={headerClassName}>Manage Account</h1>
         {error && <div className='text-red-500 text-sm'>{error}</div>}
         <div className="mb-4">
            <button className={`w-full bg-blue-500 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
                onClick={handleLogout}
                disabled={isSubmitting}>
                Logout
            </button>
        </div>
        <div className="mb-4">
            <button className={`w-full bg-blue-500 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
                onClick={handleDeleteAccount}
                disabled={isSubmitting}>
                Delete Account
            </button>
        </div>
      </div>
    );
  }
  
  export default ManageAccount;