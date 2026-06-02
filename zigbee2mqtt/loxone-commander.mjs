export default class LoxoneCommander {
    constructor(zigbee, mqtt, state, publishEntityState, eventBus,
                enableDisableExtension, restartCallback, addExtension, settings, logger) {
        this.mqtt = mqtt;
        this.eventBus = eventBus;
        this.logger = logger;
    }

    start() {
        this.mqtt.subscribe('lox/#');

        this.eventBus.onMQTTMessage(this, (data) => {
            const topic = data.topic;
            if (!topic.startsWith('lox/')) return;

            if (topic !== 'lox/WV/set' &&
                topic !== 'lox/SS/set' &&
                topic !== 'lox/LED/set' &&
                topic !== 'lox/LED/Group/set') return;

            try {
                const p = JSON.parse(data.message);

                if (topic === 'lox/WV/set') {
                    if (p.name && p.state !== undefined) {
                        this.eventBus.emitMQTTMessage({
                            topic: `Z2M/WV/${p.name}/set`,
                            message: JSON.stringify({state: p.state})
                        });
                    }
                }
                else if (topic === 'lox/SS/set') {
                    if (p.name && p.state !== undefined) {
                        this.eventBus.emitMQTTMessage({
                            topic: `Z2M/SS/${p.name}/set`,
                            message: JSON.stringify({state: p.state})
                        });
                    }
                }
                else if (topic === 'lox/LED/set') {
                    if (p.name) {
                        const cmd = {};
                        if (p.state !== undefined) cmd.state = p.state;
                        if (p.brightness !== undefined && p.brightness > 0) cmd.brightness = p.brightness;
                        if (p.color !== undefined) cmd.color = p.color;
                        this.eventBus.emitMQTTMessage({
                            topic: `Z2M/LED/${p.name}/set`,
                            message: JSON.stringify(cmd)
                        });
                    }
                }
                else if (topic === 'lox/LED/Group/set') {
                    if (p.name) {
                        const cmd = {};
                        if (p.state !== undefined) cmd.state = p.state;
                        if (p.brightness !== undefined && p.brightness > 0) cmd.brightness = p.brightness;
                        this.eventBus.emitMQTTMessage({
                            topic: `Z2M/LED/Group/${p.name}/set`,
                            message: JSON.stringify(cmd)
                        });
                    }
                }

            } catch(e) {
                this.logger.error(`LoxoneCommander error: ${e.message}`);
            }
        });
        this.logger.info('LoxoneCommander started');
    }

    stop() {
        this.eventBus.removeListeners(this);
    }
}
