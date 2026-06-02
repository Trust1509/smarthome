export default class LoxoneBridge {
    constructor(zigbee, mqtt, state, publishEntityState, eventBus,
                enableDisableExtension, restartCallback, addExtension, settings, logger) {
        this.mqtt = mqtt;
        this.eventBus = eventBus;
        this.logger = logger;
        this.cache = {};
        this.ssCache = {};
        this.ssTimer = null;
    }

    start() {
        this.eventBus.onPublishEntityState(this, (data) => {
            const name = data.entity.name;
            const p = data.payload;
            if (!this.cache[name]) this.cache[name] = {};
            Object.assign(this.cache[name], p);
            const merged = this.cache[name];
            let out = {name: name};

            if (name.startsWith('FK/') || name.startsWith('TK/')) {
                if (merged.contact !== undefined) out.contact = merged.contact ? 0 : 1;
                if (merged.battery !== undefined) out.battery = merged.battery;
                this.mqtt.publish(`lox/${name.split('/')[0]}`, JSON.stringify(out), {retain: false, qos: 0}, '');
            }
            else if (name.startsWith('BM/')) {
                if (merged.occupancy !== undefined) out.occupancy = merged.occupancy ? 1 : 0;
                if (merged.illuminance !== undefined) out.illuminance = merged.illuminance;
                if (merged.battery !== undefined) out.battery = merged.battery;
                if (merged.temperature !== undefined) out.temperature = merged.temperature;
                this.mqtt.publish('lox/BM', JSON.stringify(out), {retain: false, qos: 0}, '');
            }
            else if (name.startsWith('PM/')) {
                if (merged.presence !== undefined) out.presence = merged.presence ? 1 : 0;
                if (merged.movement !== undefined) out.movement = merged.movement === 'movement' ? 1 : 0;
                if (merged.target_distance !== undefined) out.target_distance = merged.target_distance;
                if (merged.device_temperature !== undefined) out.temperature = merged.device_temperature;
                this.mqtt.publish('lox/PM', JSON.stringify(out), {retain: false, qos: 0}, '');
            }
            else if (name.startsWith('SS/')) {
                if (!this.ssCache[name]) this.ssCache[name] = {};
                if (merged.state !== undefined) this.ssCache[name].state = merged.state === 'ON' ? 1 : 0;
                if (merged.power !== undefined) this.ssCache[name].power = merged.power;
                if (merged.device_temperature !== undefined) this.ssCache[name].temp = merged.device_temperature;

                if (!this.ssTimer) {
                    this.ssTimer = setTimeout(() => {
                        const parts = Object.entries(this.ssCache).map(([k, v]) => {
                            const n = k.replace('SS/', '');
                            return `${n}:State:${v.state ?? 0};Power:${v.power ?? 0};Temp:${v.temp ?? 0}`;
                        }).join('|');
                        this.mqtt.publish('lox/SS', parts, {retain: false, qos: 0}, '');
                        this.ssTimer = null;
                    }, 2000);
                }
            }
            else if (name.startsWith('AQ/')) {
                if (merged.humidity !== undefined) out.humidity = merged.humidity;
                if (merged.temperature !== undefined) out.temperature = merged.temperature;
                if (merged.pm25 !== undefined) out.pm25 = merged.pm25;
                if (merged.voc_index !== undefined) out.voc_index = merged.voc_index;
                this.mqtt.publish('lox/AQ', JSON.stringify(out), {retain: false, qos: 0}, '');
            }
            else if (name.startsWith('WL/')) {
                if (merged.water_leak !== undefined) out.water_leak = merged.water_leak ? 1 : 0;
                if (merged.battery !== undefined) out.battery = merged.battery;
                this.mqtt.publish('lox/WL', JSON.stringify(out), {retain: false, qos: 0}, '');
            }
            else if (name.startsWith('WV/')) {
                if (merged.state !== undefined) out.state = merged.state === 'ON' ? 1 : 0;
                if (merged.flow !== undefined) out.flow = merged.flow;
                if (merged.battery !== undefined) out.battery = merged.battery;
                this.mqtt.publish('lox/WV', JSON.stringify(out), {retain: false, qos: 0}, '');
            }
        });
        this.logger.info('LoxoneBridge started');
    }

    stop() {
        if (this.ssTimer) {
            clearTimeout(this.ssTimer);
            this.ssTimer = null;
        }
        this.eventBus.removeListeners(this);
    }
}
