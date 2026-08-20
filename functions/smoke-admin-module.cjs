const functions = require('./lib/index.js');
if (typeof functions.createOrder !== 'function') throw new Error('createOrder export missing');
if (typeof functions.adminTrusted !== 'function') throw new Error('adminTrusted export missing');
console.log('FUNCTION_EXPORTS_OK');
