import { useParams } from "react-router-dom";
import React, { useEffect, useState, useContext, useRef } from 'react';
import { AuthContext } from "./AuthContext";

function ChatMessages() {
    const bottomRef = useRef(null);
    const {chatId } = useParams();
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [isMember, setIsMember] = useState(false);
    const { token } = useContext(AuthContext);
    const [accountId, setAccountId] = useState(null);
    const [accountUsernames, setAccountUsernames] = useState({}); 
    const [editingMessageId, setEditingMessageId] = useState(null);
    const [editedText, setEditedText] = useState('');

    const handleEdit = (message) => {
        setEditingMessageId(message.id);
        setEditedText(message.text);
    };

    const handleCancelEdit = () => {
        setEditingMessageId(null);
        setEditedText('');
    };

    const handleSaveEdit = async (messageId) => {
        try {
            const response = await fetch(`http://127.0.0.1:8000/chats/${chatId}/messages/${messageId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: editedText
                }),
            });

            if(!response.ok) {
                throw new Error('Failed to update message');
            }
            const updatedMessage = await response.json();

            setMessages((prevMessages) => 
                prevMessages.map((msg) => (msg.id == messageId ? updatedMessage : msg))
            );
              

            setEditingMessageId(null);
            setEditedText('');
        }
        catch (error) {
            console.error('Error saving edit: ', error);
        }
    };

    const handleDelete = async (messageId) => {
        try {
            const response = await fetch(`http://127.0.0.1:8000/chats/${chatId}/messages/${messageId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    "Content-Type": 'application/json',
                },
            });

            if(!response.ok){
                throw new Error('Failed to delete message');
            }

            setMessages((prevMessages) => prevMessages.filter((msg) => msg.id !== messageId));
        }
        catch (error){
            console.error('Error deleting message: ', error);
        }
    }

    const fetchAccountUsername = async (chatAccountId) => {
        if(accountUsernames[chatAccountId]) {
            return accountUsernames[chatAccountId];
        }
        try {
            const response = await fetch(`http://127.0.0.1:8000/accounts/${chatAccountId}`)
            if(!response.ok) {
                throw new Error("Failed to get username");
            }
            const account = await response.json();
            setAccountUsernames(prev => ({ ...prev, [chatAccountId]: account.username}));
            return account.username;
        }
        catch (error) {
            console.error(`Error getting username for ${chatAccountId}: `, error );
            return '[removed]';
        }
    }

    useEffect(() => {
        bottomRef.current?.scrollIntoView({
            behavior: 'smooth'
        });
    }, [messages]);

    //check if member 
    useEffect(() => {
        if(!chatId || !accountId) return;

        const checkMembership = async () => {
            try {
                const response = await fetch(`http://127.0.0.1:8000/chats/${chatId}/accounts`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                });

                if (!response.ok) {
                    throw new Error('Failed to get chat membership');
                }

                const data = await response.json();
                const isUserMember = data.accounts.some(account => account.id === accountId);
                setIsMember(isUserMember);
            }
            catch (error) {
                console.error('Error checking membership: ', error);
            }
        };
        checkMembership();
    }, [chatId, accountId, token]);

    //Get current user
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
                    setAccountId(user.id);
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

    //Get messages
    useEffect(() => {
        fetch(`http://127.0.0.1:8000/chats/${chatId}/messages`)
            .then(response => {
                if(!response.ok) {
                    throw new Error("NOT OK");
                }
                return response.json();
            })
            .then(data => {
                setMessages(data.messages);

                data.messages.forEach(message => {
                    if(!accountUsernames[message.account_id]) {
                        fetchAccountUsername(message.account_id);
                    }
                });
            })

            .catch(error => console.error("Couldn't get chat messages", error));
    }, [chatId, accountUsernames]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if(!newMessage.trim()){
            return;
        }
        try {
            const response = await fetch(`http://127.0.0.1:8000/chats/${chatId}/messages`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    "text": newMessage,
                    "account_id": accountId,
                }),
            });

            if(!response.ok) throw new Error("Failed to send message");
            const data = await response.json();

            setMessages((prev) => [...prev, data]);
            setNewMessage("");
        }
        catch (error) {
            console.error("Send message error: ", error);
        }
    }
    return (
        <div className="flex flex-col h-screen">
            <div className=" flex-1 space-y-4 overflow-y-auto p-4 pb-4 h-[calc(100lvh-{value}px)]">
                {messages.length === 0 ? (
                    <div className="text-center text-xl font-semibold text-gray-500">
                        No chat messages
                    </div>
                ) : (
                    messages.map((message) => (
                        <div
                            key={message.id}
                            className="bg-white p-4 rounded shadow-lg space-y-2"
                        >
                        {editingMessageId === message.id ? (
                            <>
                                <div className="font-semibold">
                                    Editing Message - {new Date(message.created_at).toLocaleString()}
                                </div>
                                <input
                                    type="text"
                                    value={editedText}
                                    onChange={(e) => setEditedText(e.target.value)}
                                    className="w-full p-2 rounded"
                                />
                                <div className="flex space-x-2 pt-2">
                                    <button
                                        onClick={() => handleSaveEdit(message.id)}
                                        className="px-3 py-1 bg-emerald-300 text-white rounded hover:bg-emerald-600"
                                    >
                                        Save
                                    </button>
                                    <button
                                        onClick={handleCancelEdit}
                                        className="px-3 py-1 bg-gray-300 text-black rounded hover:bg-gray-400"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="font-semibold">
                                    {message.account_id && accountUsernames[message.account_id]
                                        ? accountUsernames[message.account_id]
                                        : 'loading...'} -{' '}
                                    {new Date(message.created_at).toLocaleString()}
                                </div>
                                <div>{message.text}</div>
                                {message.account_id === accountId && (
                                    <div className="flex space-x-2 pt-2">
                                        <button
                                            onClick={() => handleEdit(message)}
                                            className="px-3 py-1 bg-yellow-200 text-black rounded hover:bg-yellow-400"
                                        >
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => handleDelete(message.id)}
                                            className="px-3 py-1 bg-rose-400 text-white rounded hover:bg-rose-600"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                )}
                            </>
                        )}

                        </div>
                    ))
                )}
                <div ref={bottomRef}/>
            </div>

            {isMember && (
                <form onSubmit={handleSendMessage} className="flex items-center bg-white py-4">
                    <input
                        type="text"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        className="flex-1 round px-4 py-2 mr-2"
                        placeholder="New message...">
                    </input>
                    <button
                        type="submit"
                        disabled={!newMessage.trim()}
                        className={`px-4 py-2 rounded text-white 
                                    ${newMessage.trim() 
                                        ? "bg-blue-500 hover:bg-blue-600" 
                                        : "bg-gray-400 cursor-not-allowed"}`}>
                        Send
                    </button>
                </form>
            )}
        </div>
    );
  }
  
  export default ChatMessages;