const http = require('node:http');

// Z2M 2.14.2's MQTT health_check returns a constant true. Track the
// adapterDisconnected event instead, including when shutdown gets stuck.
module.exports = class AdapterHealth {
    constructor(zigbee, mqtt, state, publishEntityState, eventBus) {
        this.eventBus = eventBus;
        this.healthy = false;
    }

    async start() {
        this.eventBus.onAdapterDisconnected(this, () => { this.healthy = false; });
        // Extensions start only after the coordinator has initialized.
        this.healthy = true;
        this.server = http.createServer((request, response) => {
            if (request.url !== '/healthz') {
                response.writeHead(404).end();
                return;
            }
            response.writeHead(this.healthy ? 200 : 503, {'Content-Type': 'text/plain'});
            response.end(this.healthy ? 'Adapter connected\n' : 'Adapter disconnected\n');
        });
        await new Promise((resolve, reject) => {
            this.server.once('error', reject);
            this.server.listen(9001, '0.0.0.0', resolve);
        });
    }

    async stop() {
        this.healthy = false;
        this.eventBus.removeListeners(this);
        if (this.server) {
            await new Promise((resolve) => this.server.close(resolve));
        }
    }
};
