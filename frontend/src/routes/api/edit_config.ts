// import { readFileSync, writeFileSync } from 'fs'

const config_file_path = '.storage/config.yaml'

export function get(request) {
    const data = readFileSync(config_file_path, 'utf-8')
    return {
        body: data
    }
}


// export async function post(request) {
//     console.log(request)
//     const body = JSON.parse(request)
//     console.log(body)

//     writeFileSync(config_file_path, body)
//     console.log('Post success!');

//     return;
// }

export async function post({ request }) {
    // console.log(request)
    // const content = JSON.stringify(request)
    // console.log('log of request : ', data);
    const content = await request.json()
    writeFileSync(config_file_path, content)
    return;
}