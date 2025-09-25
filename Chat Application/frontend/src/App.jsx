import { BrowserRouter, Routes, Route, Outlet, Navigate } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthContext, AuthProvider } from "./AuthContext";
import Chats from "./Chats";
import ChatMessages from "./ChatMessages";
import Login from "./Login";
import SignUp from "./SignUp";
import ManageAccount from "./ManageAccount";
import UpdateAccount from "./UpdateAccount";
import UpdatePassword from "./UpdatePassword";
import Account from "./Account";
import { useContext } from "react";

const headerClassName = "text-center text-4xl font-extrabold py-4";

const queryClient = new QueryClient();

function ProtectedRoute(){
  const { loggedIn } = useContext(AuthContext);

  if(!loggedIn) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

function NotFound() {
  return <h1 className={headerClassName}>404: Not Found</h1>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="login" element={<Login />} />
            <Route path="register" element={<SignUp />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<SideBar />}>
                <Route path="chats/:chatId" element={<ChatMessages />} />
                <Route path="accounts/me" element={<UpdateAccount />} />
                <Route path="accounts/me/password" element={<UpdatePassword />} />
                <Route path="accounts/manage" element={<ManageAccount />} />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

function ChatLayout() {
  return (
    <div className="flex imma2">
        <Chats />
    </div>
  );
}

function SettingsLayout() {
  return (
    <div className="flex imma 1">
        <Account />
    </div>
  );
}

function SideBar() {
  return(
    <div className="flex imma2">
    <div className="w-1/4 p-4 border-r border-gray-300">
      <ChatLayout />
      <SettingsLayout />
    </div>
    <div className="w-3/4 p-4 overflow-y-auto">
      <Outlet />
    </div>
  </div>
  )
}


export default App;
