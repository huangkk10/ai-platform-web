import React, { createContext, useContext, useState } from 'react';

const ChatContext = createContext();

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  const [clearChatFunction, setClearChatFunction] = useState(null);

  const registerClearFunction = (clearFn) => {
    setClearChatFunction(() => clearFn);
  };

  const clearClearFunction = () => {
    setClearChatFunction(null);
  };

  return (
    <ChatContext.Provider value={{
      clearChatFunction,
      registerClearFunction,
      clearClearFunction
    }}>
      {children}
    </ChatContext.Provider>
  );
};