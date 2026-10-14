// Forward a local TCP port to a service on the Docker host.
// Use when the app's backing service runs on the host and advertises "localhost"
// (e.g. Kafka advertised.listeners=localhost): the app dials localhost inside the
// container, and this relays it to the host so partition/leader traffic reaches it.
//
//   node tcp-forward.mjs [localPort=9092] [upstreamHost=host.docker.internal] [upstreamPort=localPort]
//
// Run in the background; it serves all connections (one upstream per client),
// which is enough for a single-broker / single-node service during a demo.
import net from 'node:net';

const LISTEN = Number(process.argv[2] || 9092);
const UP_HOST = process.argv[3] || 'host.docker.internal';
const UP_PORT = Number(process.argv[4] || LISTEN);

net
  .createServer((cli) => {
    const up = net.connect({ host: UP_HOST, port: UP_PORT });
    cli.pipe(up);
    up.pipe(cli);
    const kill = () => {
      cli.destroy();
      up.destroy();
    };
    cli.on('error', kill);
    up.on('error', kill);
  })
  .listen(LISTEN, '127.0.0.1', () =>
    console.error(`forward 127.0.0.1:${LISTEN} -> ${UP_HOST}:${UP_PORT}`),
  );
