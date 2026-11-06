const {test} = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const AdapterHealth = require('../kubernetes/apps/home-automation/zigbee2mqtt/app/adapter-health.cjs');

function request(path = '/healthz') {
    return new Promise((resolve, reject) => {
        http.get(`http://127.0.0.1:9001${path}`, {agent: false}, (response) => {
            response.resume();
            response.on('end', () => resolve(response.statusCode));
        }).on('error', reject);
    });
}

test('disconnect stays unhealthy until reinitialization, even if MQTT stays online', async () => {
    let disconnected;
    const eventBus = {
        onAdapterDisconnected(owner, callback) { disconnected = callback; },
        removeListeners() { disconnected = undefined; },
    };
    const extension = new AdapterHealth(null, null, null, null, eventBus);
    try {
        await extension.start();
        assert.equal(await request(), 200);
        assert.equal(await request('/other'), 404);
        disconnected();
        assert.equal(await request(), 503);
        assert.equal(await request(), 503);
        await extension.stop();
        assert.equal(disconnected, undefined);
        await assert.rejects(request(), {code: 'ECONNREFUSED'});
        await extension.start();
        assert.equal(await request(), 200);
    } finally {
        await extension.stop();
    }
});
