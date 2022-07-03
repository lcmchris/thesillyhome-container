import { spawnSync } from 'child_process';

export async function post({ request }) {
    const body = await request.json()

    const child = spawnSync(body.program, body.command)
    console.log(`Process started with ${body.program, body.command}`);

    if (child.status !== 0) {

        const response = child.stderr.toString()
        console.log(response)
        return { body: response }

    }
    else {

        const response = child.stdout.toString()
        console.log(response)
        return { body: response }
    }
}
