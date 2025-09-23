import React, { createContext, useState, useEffect } from 'react';

const AuthContext = createContext();

const AuthProvider = ({ children }) => {
    const storedToken = localStorage.getItem('authToken');
    const [token, setToken] = useState(storedToken);
    const [loggedIn, setLoggedIn] = useState(!!storedToken);

    const login = (newToken) => {
        setToken(newToken);
        setLoggedIn(true);
        localStorage.setItem('authToken', newToken);
    }

    const logout = () => {
        setToken(null);
        setLoggedIn(false);
        localStorage.removeItem('authToken');
    }

    return (
        <AuthContext.Provider value={{ loggedIn, token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export { AuthContext, AuthProvider };