import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from "./AuthContext";

const headerClassName = "text-center text-4xl font-extrabold py-4";

function UpdateAccount() {
    const { token } = useContext(AuthContext);
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

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
                    setEmail(user.email);
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

    const handleSubmit = async (event) => {
        event.PreventDefault();
        setIsSubmitting(true);
        setError('');

        const updateData = { username, email };

        try {
            const response = await fetch('http://127.0.0.1:8000/accounts/me', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updateData),
            });
            if(response.ok){
                const data = await response.json();
                console.log('User updated successfully', data);
            }
            else {
                const errorData = await response.json();
                setError(errorData.detail || "Something went wrong");
            }
        }
        catch (error) {
            setError("Failed to update account");
        }
        finally {
            setIsSubmitting(false);
        }
    }
    
    const isFormValid = username.trim() && email.trim();

    return (
    
      <div>
         <h1 className={headerClassName}>Update Account</h1>
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
                    <label htmlFor="email" className="mb-2 text-sm font-medium text-gray-700">Email</label>
                    <input 
                        type="text" 
                        id="email" 
                        name="email" 
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
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
                            {isSubmitting ? 'Updating...' : 'Update'}
                    </button>
                </div>
            </form>
        </div>
      </div>
    );
  }
  
  export default UpdateAccount;