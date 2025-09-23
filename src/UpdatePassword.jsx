import { NavLink, useLocation } from "react-router";
import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from "./AuthContext";

const headerClassName = "text-center text-4xl font-extrabold py-4";

function UpdatePassword() {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmNewPassword, setConfirmNewPassword] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { token } = useContext(AuthContext);


    const isFormValid = newPassword && confirmNewPassword && newPassword == confirmNewPassword;

    const handleSubmit = async (event) => {
        event.preventDefault();
        if(!isFormValid) {
            setError('Passwords do not match');
            return;
        }

        setIsSubmitting(true);
        setError('');

        const formData = new URLSearchParams();
        formData.append('old_password', currentPassword);
        formData.append('new_password', newPassword)

        try{
            const reponse = await fetch('http://127.0.0.1:8000/accounts/me/password', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': `Bearer ${token}`,
                },
                body: formData.toString(),
            });

            if(!reponse.ok){
                const errorData = await response.json();
                setError(errorData.message || 'Failed to update password');
                return;
            }
        }
        catch (error){
            setError(error.message);
        }
        finally {
            setIsSubmitting(false);
        }
    }

    return (
    
      <div>
         <h1 className={headerClassName}>Update Password</h1>
         <div className="flex items-center justify-center">
            <form onSubmit={handleSubmit} className="p-8 bg-gray-200 rounded w-full max-w-sm space-y-6">
                <div className="flex flex-col">
                    <label htmlFor="currPass" className="mb-2 text-sm font-medium text-gray-700">Current Password</label>
                    <input 
                        type="password" 
                        id="currPass" 
                        name="currPass" 
                        value={currentPassword} 
                        onChange={(e) => setCurrentPassword(e.target.value)} 
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                        required>
                    </input>
                </div>

                <div className="flex flex-col">
                    <label htmlFor="newPass" className="mb-2 text-sm font-medium text-gray-700">New Password</label>
                    <input 
                        type="password" 
                        id="newPass" 
                        name="newPass" 
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                        required>
                    </input>
                </div>

                <div className="flex flex-col">
                    <label htmlFor="confirmNewPass" className="mb-2 text-sm font-medium text-gray-700">Confirm New Password</label>
                    <input 
                        type="password" 
                        id="confirmNewPass" 
                        name="confirmNewPass" 
                        value={confirmNewPassword}
                        onChange={(e) => setConfirmNewPassword(e.target.value)}
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
                            {isSubmitting ? 'Updating...' : 'Update Password'}
                    </button>
                </div>
            </form>
        </div>
      </div>
    );
  }
  
  export default UpdatePassword;