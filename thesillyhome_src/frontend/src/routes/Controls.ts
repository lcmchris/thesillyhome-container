import { exec, spawn, spawnSync } from 'child_process';
import socket from 'socket.io'

// export async function post({ request }) {
//     const body = await request.json()
//     console.log(`Process started with ${body.program, body.command}`);

//     const child = spawnSync(body.program, body.command)

//     if (child.status !== 0) {

//         const response = child.stderr.toString()
//         console.log(response)
//         return { body: response }

//     }
//     else {

//         const response = child.stdout.toString()
//         console.log(response)
//         return { body: response }
//     }
// }

export async function post({ request }) {
    const body = await request.json()
    console.log(`Process started with ${body.program, body.command}`);

    const child = spawn(body.program, body.command)

    child.stdout.on('data', function (data) {
        socket.emit('consoleWrite', data + '');
    });

    child.stderr.on('data', function (data) {
        socket.emit('consoleWrite', data + '');
    });

}

