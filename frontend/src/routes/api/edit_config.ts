import { readFile } from 'fs'

export function get() {

    readFile('../.storage/config.yaml', 'utf8', (err, data) => {
        if (err) {
            console.error(err);
            return;
        }
        console.log(data);
    });
}


