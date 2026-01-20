console.log('=== Environment Variables Test ===');
console.log('REACT_APP_DEPLOY_ENV:', process.env.REACT_APP_DEPLOY_ENV);
console.log('REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('All REACT_APP_* vars:', Object.keys(process.env).filter(k => k.startsWith('REACT_APP_')));
