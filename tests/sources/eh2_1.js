export default (request) => {
    console.log('Event Handler #2 (altered)')
    const pubnub = require('pubnub');
    const kvstore = require('kvstore');
    const xhr = require('xhr');

    console.log(request); // Log the request envelope passed
    return request.ok(); // Return a promise when you're done
}