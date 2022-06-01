import { readFile } from 'fs'

export function get(request) {

    readFile('../.storage/config.yaml', 'utf8', (err, data) => {
        if (err) {
            console.error(err);
            return;
        }
        console.log(data);
    });
}

export function post(request) {
    return {
        body: { bye: 'world', request: request.body }
    }
}


