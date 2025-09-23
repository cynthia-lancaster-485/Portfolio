import { NavLink, useLocation } from "react-router";
import React, { useEffect, useState } from 'react';

const headerClassName = "text-center text-4xl font-extrabold py-4";

function Chats() {
    const location = useLocation();
    
    const [chatList, setChatList] = useState([]);

    useEffect(() => {
        fetch('http://127.0.0.1:8000/chats')
            .then(response => {
                console.log("Response:", response);
                if(!response.ok) {
                    throw new Error("NOT OK");
                }
                return response.json();
            })
            .then(data => setChatList(data.chats))
            .catch(error => console.error("Couldn't get chat list:", error));
    }, []);


    return (
    
      <div>
         <h1 className={headerClassName}>Pony Express</h1>
         <div className="space-y-2">
            <h3><strong>Chats</strong></h3>
         {chatList
            .sort((a, b) => a.name.localeCompare(b.name))
            .map((chat) => {
                const isActive = location.pathname === `/chats/${chat.id}`;
                return (
                    <NavLink
                        key={chat.id}
                        to={`/chats/${chat.id}`}
                        className={`block px-4 rounded ${
                            isActive 
                            ? "bg-blue-500 text-white font-bold"
                            : "hover:bg-black hover:text-white"
                        }`}
                    >
                        {chat.name}
                    </NavLink>
                );
            })}
         </div>
      </div>
    );
  }
  
  export default Chats;